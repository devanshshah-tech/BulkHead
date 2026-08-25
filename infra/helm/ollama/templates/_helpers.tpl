{{- define "ollama.name" -}}
ollama
{{- end -}}

{{- define "ollama.labels" -}}
app.kubernetes.io/name: {{ include "ollama.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: bulkhead
{{- end -}}
