{{- define "signal-ingestion.fullname" -}}
{{ include "signal-ingestion.name" . }}
{{- end -}}

{{- define "signal-ingestion.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "signal-ingestion.labels" -}}
app.kubernetes.io/name: {{ include "signal-ingestion.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "signal-ingestion.selectorLabels" -}}
app.kubernetes.io/name: {{ include "signal-ingestion.name" . }}
{{- end -}}
