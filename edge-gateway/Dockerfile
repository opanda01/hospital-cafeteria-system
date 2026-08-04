FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN go mod tidy && CGO_ENABLED=0 go build -o /gateway ./cmd/gateway

FROM alpine:3.20
WORKDIR /app
RUN mkdir -p /app/data
COPY --from=build /gateway /app/gateway
EXPOSE 9000 9090
CMD ["/app/gateway"]
