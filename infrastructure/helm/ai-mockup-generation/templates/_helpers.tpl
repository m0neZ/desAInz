{{- define "ai-mockup-generation.fullname" -}}
{{ include "ai-mockup-generation.name" . }}
{{- end -}}

{{- define "ai-mockup-generation.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "ai-mockup-generation.labels" -}}
app.kubernetes.io/name: {{ include "ai-mockup-generation.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "ai-mockup-generation.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ai-mockup-generation.name" . }}
{{- end -}}
