# Use Node runtime as parent image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy dependency definition files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Expose port 5173 for Vite Dev Server
EXPOSE 5173

# Run Vite in host mode so it's accessible externally
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
