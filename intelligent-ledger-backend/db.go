package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// DBClient holds our active PostgreSQL connection pool
var DBClient *pgxpool.Pool

// InitDB initializes a thread-safe connection pool to Supabase with retry logic
func InitDB() {
	// Retrieve the connection string from environment variables
	connString := os.Getenv("DATABASE_URL")
	if connString == "" {
		log.Fatal("DATABASE_URL environment variable is empty or not set")
	}

	// Retry configuration for connection establishment
	maxRetries := 5
	retryDelay := 2 * time.Second

	for attempt := 1; attempt <= maxRetries; attempt++ {
		// Configure the pool settings
		config, err := pgxpool.ParseConfig(connString)
		if err != nil {
			log.Printf("Attempt %d/%d: Unable to parse database connection string: %v", attempt, maxRetries, err)
			if attempt < maxRetries {
				time.Sleep(retryDelay)
				continue
			}
			log.Fatalf("CRITICAL: Failed to parse database connection after %d attempts: %v", maxRetries, err)
		}

		// Enterprise Tuning parameters
		config.MaxConns = 25                      // Maximum number of active connections
		config.MinConns = 5                       // Minimum idle connections kept warm
		config.MaxConnIdleTime = 30 * time.Minute // Clean up stale connections

		// Create the pool with timeout
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		DBClient, err = pgxpool.NewWithConfig(ctx, config)
		cancel()

		if err != nil {
			log.Printf("Attempt %d/%d: Unable to create database connection pool: %v", attempt, maxRetries, err)
			if attempt < maxRetries {
				time.Sleep(retryDelay)
				continue
			}
			log.Fatalf("CRITICAL: Unable to create database connection pool after %d attempts: %v", maxRetries, err)
		}

		// Verify the connection with timeout
		pingCtx, pingCancel := context.WithTimeout(context.Background(), 5*time.Second)
		err = DBClient.Ping(pingCtx)
		pingCancel()

		if err != nil {
			log.Printf("Attempt %d/%d: Database ping failed: %v", attempt, maxRetries, err)
			if DBClient != nil {
				DBClient.Close()
			}
			if attempt < maxRetries {
				time.Sleep(retryDelay)
				continue
			}
			log.Fatalf("CRITICAL: Supabase database connection failed after %d attempts. Check credentials or network access. Error: %v", maxRetries, err)
		}

		// Success!
		fmt.Println("✓ Successfully connected to Supabase and established connection pool.")
		return
	}
}