{{- define "feedback-loop.fullname" -}}
{{ include "feedback-loop.name" . }}
{{- end -}}

{{- define "feedback-loop.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "feedback-loop.labels" -}}
app.kubernetes.io/name: {{ include "feedback-loop.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "feedback-loop.selectorLabels" -}}
app.kubernetes.io/name: {{ include "feedback-loop.name" . }}
{{- end -}}
