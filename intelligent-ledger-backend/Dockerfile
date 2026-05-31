# Upgrade the build layer to use Go 1.25 to match your go.mod constraints
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Cache dependencies layers cleanly
COPY go.mod go.sum ./
RUN go mod download

# Bring in the complete source matrix
COPY . .

# Compile a statically-linked, minimalist binary production build
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Production scratch environment runner image
FROM alpine:latest  
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]