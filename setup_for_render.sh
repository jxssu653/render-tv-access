#!/bin/bash
# Setup script for Render deployment

echo "🚀 Setting up TradingView Access Manager for Render deployment..."

# Copy requirements file
echo "📦 Copying requirements file..."
cp render_requirements.txt requirements.txt

# Create .env file from current environment
echo "🔧 Creating .env file..."
python secrets_to_env.py

# Show deployment checklist
echo ""
echo "✅ Setup complete! Next steps:"
echo ""
echo "1. Push your code to GitHub repository"
echo "2. Go to Render Dashboard (render.com)"
echo "3. Create new Blueprint from your GitHub repo"
echo "4. Render will automatically detect render.yaml"
echo "5. Set environment variables in Render dashboard:"
echo "   - TRADINGVIEW_USERNAME"
echo "   - TRADINGVIEW_PASSWORD"
echo "   - SESSION_SECRET (generated below)"
echo ""
echo "🔑 Suggested SESSION_SECRET:"
python -c "import secrets; print('   ' + secrets.token_hex(32))"
echo ""
echo "📖 For detailed instructions, see deploy_instructions.md"
echo "🌐 Your app will be available at: https://your-service-name.onrender.com"