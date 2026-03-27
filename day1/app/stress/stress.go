package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func newResponseWriter(w http.ResponseWriter) *responseWriter {
	return &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// loggingMiddleware logs method, path, status code, remote addr, and duration
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rw := newResponseWriter(w)

		next.ServeHTTP(rw, r)

		log.Printf("[ACCESS] %s %s %s %d %s",
			r.RemoteAddr,
			r.Method,
			r.URL.String(),
			rw.statusCode,
			time.Since(start),
		)
	})
}

func stressPostHandler(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Iterator int `json:"iterator"`
	}

	if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Iterator <= 0 {
		body.Iterator = 1000
	}

	// CPU stress: perform floating-point arithmetic iterations
	result := 1.0
	for i := 0; i < body.Iterator; i++ {
		result *= 1.0000001
		result /= 1.0000001
	}
	_ = result

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"message": "The cpu is loaded"})
}

func stressGetHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"version": "v1.0"})
}

func stressHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodPost:
		stressPostHandler(w, r)
	case http.MethodGet:
		stressGetHandler(w, r)
	default:
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
	}
}

func healthcheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/stress", stressHandler)
	mux.HandleFunc("/healthcheck", healthcheckHandler)

	log.Println("Stress application starting on :8080")
	srv := &http.Server{
		Addr:         ":8080",
		Handler:      loggingMiddleware(mux),
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	if err := srv.ListenAndServe(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
