"use server";

import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
});

export interface Transaction {
  id: string;
  user_id: string;
  raw_text: string;
  clean_name: string | null;
  category: string | null;
  amount: number;
  currency: string;
  status: "PENDING" | "PROCESSED" | "FLAGGED_ANOMALY";
  transaction_timestamp: string;
  created_at: string;
}

export async function getTransactions(): Promise<Transaction[]> {
  try {
    const result = await pool.query(`
      SELECT
        id,
        user_id,
        raw_text,
        clean_name,
        category,
        amount::float as amount,
        currency,
        status,
        transaction_timestamp::text,
        created_at::text
      FROM transactions
      ORDER BY transaction_timestamp DESC
      LIMIT 50;
    `);

    return result.rows;
  } catch (error) {
    console.error("Direct server fetch execution tracking failure:", error);
    return [];
  }
}

export async function submitTransaction(payload: {
  user_id: string;
  raw_text: string;
  amount: number;
  currency: string;
  transaction_timestamp: string;
}) {
  try {
    const response = await fetch("http://localhost:8080/api/v1/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(
        `Gateway boundary returned invalid tracking state: ${response.status}`,
      );
    }

    return { success: true };
  } catch (error) {
    console.error("Network gateway transit dropped link execution:", error);
    return { success: false, error: String(error) };
  }
}
