package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/segmentio/kafka-go"
)

// KafkaWriter is the global, thread-safe producer instance
var KafkaWriter *kafka.Writer

// TransactionEvent is the structured message contract we pass down the conveyor belt
type TransactionEvent struct {
	TransactionID string  `json:"transaction_id"`
	RawText       string  `json:"raw_text"`
	Amount        float64 `json:"amount"`
}

// InitKafka initializes our high-throughput production event producer
func InitKafka() {
	broker := os.Getenv("KAFKA_BROKER")
	topic := os.Getenv("KAFKA_TOPIC")
	if broker == "" {
		log.Println("WARNING: KAFKA_BROKER environment variable not set, Kafka producer may not work correctly")
		broker = "kafka:29092" // fallback
	}
	if topic == "" {
		log.Println("WARNING: KAFKA_TOPIC environment variable not set, Kafka producer may not work correctly")
		topic = "transaction-signals" // fallback
	}

	// Configure the writer with enterprise tuning defaults
	KafkaWriter = &kafka.Writer{
		Addr:         kafka.TCP(broker),
		Topic:        topic,
		Balancer:     &kafka.LeastBytes{}, // Evenly balance event messages across partitions
		MaxAttempts:  3,                   // Retries on temporary network drops
		WriteTimeout: 10 * time.Second,
		ReadTimeout:  10 * time.Second,
		Async:        false, // Set to false for synchronous acknowledgments of delivery safety
	}

	fmt.Printf("✓ Kafka Producer initialized on broker: %s, topic: %s\n", broker, topic)
}