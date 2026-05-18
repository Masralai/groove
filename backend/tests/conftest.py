import os

# Set environment variables before any imports
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test-key"
os.environ["OPENROUTER_MODEL"] = "test-model"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_db"
