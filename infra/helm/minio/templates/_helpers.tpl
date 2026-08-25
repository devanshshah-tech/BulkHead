{{- define "minio.name" -}}
minio
{{- end -}}

{{- define "minio.labels" -}}
app.kubernetes.io/name: {{ include "minio.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: bulkhead
{{- end -}}
