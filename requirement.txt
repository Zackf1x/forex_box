# Use an official Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only needed files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir python-telegram-bot matplotlib pandas numpy python-dotenv

# Run your bot
CMD ["python", "forex_bot.py"]
