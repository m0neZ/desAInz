{{- define "analytics.fullname" -}}
{{ include "analytics.name" . }}
{{- end -}}

{{- define "analytics.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "analytics.labels" -}}
app.kubernetes.io/name: {{ include "analytics.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "analytics.selectorLabels" -}}
app.kubernetes.io/name: {{ include "analytics.name" . }}
{{- end -}}
