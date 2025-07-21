{{- define "monitoring.fullname" -}}
{{ include "monitoring.name" . }}
{{- end -}}

{{- define "monitoring.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "monitoring.labels" -}}
app.kubernetes.io/name: {{ include "monitoring.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "monitoring.selectorLabels" -}}
app.kubernetes.io/name: {{ include "monitoring.name" . }}
{{- end -}}
