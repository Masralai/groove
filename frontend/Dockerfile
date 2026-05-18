ARG API_URL=http://localhost:8000

FROM node:20-alpine AS builder
ARG API_URL
ENV API_URL=$API_URL
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Install curl for healthcheck
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -S -g 1001 nodegroup && \
    adduser -S -u 1001 -G nodegroup nodeuser

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nodeuser:nodegroup /app/public ./public

# Switch to non-root user
USER 1001

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
