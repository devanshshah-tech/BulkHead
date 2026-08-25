package store

import "testing"

func TestVectorLiteral(t *testing.T) {
	got := VectorLiteral([]float32{0.5, -1, 0.25})
	want := "[0.5,-1,0.25]"
	if got != want {
		t.Fatalf("VectorLiteral = %q, want %q", got, want)
	}
	if got := VectorLiteral(nil); got != "[]" {
		t.Fatalf("VectorLiteral(nil) = %q, want []", got)
	}
}
