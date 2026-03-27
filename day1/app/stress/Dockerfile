FROM --platform=$BUILDPLATFORM public.ecr.aws/docker/library/golang:alpine AS builder

ARG TARGETOS
ARG TARGETARCH

WORKDIR /build

COPY stress.go ./

RUN go mod init stress && go mod tidy

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o stress .

FROM public.ecr.aws/docker/library/alpine

WORKDIR /app

COPY --from=builder /build/stress .

RUN apk --no-cache add curl

CMD ["./stress"]