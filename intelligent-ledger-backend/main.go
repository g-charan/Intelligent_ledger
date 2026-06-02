package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/segmentio/kafka-go"
)

type TransactionStatus string

const (
	StatusPending        TransactionStatus = "PENDING"
	StatusProcessed      TransactionStatus = "PROCESSED"
	StatusFlaggedAnomaly TransactionStatus = "FLAGGED_ANOMALY"
)

type Transaction struct {
	ID                   uuid.UUID         `json:"id"`
	UserID               uuid.UUID         `json:"user_id"`
	RawText              string            `json:"raw_text"`
	CleanName            string            `json:"clean_name,omitempty"`
	Category             string            `json:"category,omitempty"`
	Amount               float64           `json:"amount"`
	Currency             string            `json:"currency"`
	Status               TransactionStatus `json:"status"`
	TransactionTimestamp time.Time         `json:"transaction_timestamp"`
	CreatedAt            time.Time         `json:"created_at"`
}

type IngestRequest struct {
	UserID               string    `json:"user_id" binding:"required"`
	RawText              string    `json:"raw_text" binding:"required"`
	Amount               float64   `json:"amount" binding:"required"`
	Currency             string    `json:"currency" binding:"required"`
	TransactionTimestamp time.Time `json:"transaction_timestamp" binding:"required"`
}

func main() {
	// For local testing, ensure your env is set or loaded manually.
	// In production, your Docker container or environment manager sets this.
	if os.Getenv("DATABASE_URL") == "" {
		// Mock local fallback for local development testing
		os.Setenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/postgres")
	}

	// Initialize Supabase Connection
	InitDB()
	defer DBClient.Close()

	// Initialize Kafka Producer for async event streaming
	InitKafka()
	defer KafkaWriter.Close()

	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	router.POST("/api/v1/transactions", handleIngest)

	router.Run(":8080")
}

func handleIngest(c *gin.Context) {
	var req IngestRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload", "details": err.Error()})
		return
	}

	userUUID, err := uuid.Parse(req.UserID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id format"})
		return
	}

	// Assemble the structural entity
	tx := Transaction{
		ID:                   uuid.New(),
		UserID:               userUUID,
		RawText:              req.RawText,
		Amount:               req.Amount,
		Currency:             req.Currency,
		Status:               StatusPending,
		TransactionTimestamp: req.TransactionTimestamp,
		CreatedAt:            time.Now(),
	}

	// Execute high-speed raw SQL insert into Supabase
	query := `
		INSERT INTO transactions (id, user_id, raw_text, amount, currency, status, transaction_timestamp, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
	`

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	_, err = DBClient.Exec(ctx, query, tx.ID, tx.UserID, tx.RawText, tx.Amount, tx.Currency, tx.Status, tx.TransactionTimestamp, tx.CreatedAt)
	if err != nil {
		// If the database fails, return a 500 error immediately to keep data integral
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to persist transaction to ledger", "details": err.Error()})
		return
	}

	// Broadcast this exact tx.ID and raw_text out to Kafka for our Python ML workers
	event := TransactionEvent{
		TransactionID: tx.ID.String(),
		RawText:       tx.RawText,
		Amount:        tx.Amount,
	}
	
	eventBytes, _ := json.Marshal(event)
	err = KafkaWriter.WriteMessages(ctx, kafka.Message{
		Value: eventBytes,
	})
	if err != nil {
		// Log Kafka errors but don't fail the response — database write succeeded
		fmt.Printf("[KAFKA ERROR] Failed to publish transaction event: %v\n", err)
	}

	c.JSON(http.StatusAccepted, gin.H{
		"status":      "stored_and_pending",
		"transaction": tx,
	})
}