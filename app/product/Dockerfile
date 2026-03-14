FROM --platform=$BUILDPLATFORM public.ecr.aws/docker/library/golang:alpine AS builder

ARG TARGETOS
ARG TARGETARCH

WORKDIR /build

COPY product.go ./

RUN go mod init product && go mod tidy

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o product .

FROM public.ecr.aws/docker/library/alpine

WORKDIR /app

COPY --from=builder /build/product .

RUN apk --no-cache add curl

CMD ["./product"]