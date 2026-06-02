const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres.ltyrbhvpnwzthbvchyau:R7WDQHxouRQCfzhQ@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres'
});

client.connect();
client.query(
  "SELECT id, raw_text, clean_name, category, status FROM transactions WHERE raw_text LIKE '%CURSOR%' ORDER BY created_at DESC LIMIT 1",
  (err, res) => {
    if (err) console.error('Query error:', err);
    else {
      console.log('Latest CURSOR transaction:');
      console.log(JSON.stringify(res.rows[0], null, 2));
    }
    client.end();
  }
);
