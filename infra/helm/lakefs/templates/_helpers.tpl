{{- define "lakefs.name" -}}
lakefs
{{- end -}}

{{- define "lakefs.labels" -}}
app.kubernetes.io/name: {{ include "lakefs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: bulkhead
{{- end -}}
