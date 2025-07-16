{{- define "scoring-engine.fullname" -}}
{{ include "scoring-engine.name" . }}
{{- end -}}

{{- define "scoring-engine.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "scoring-engine.labels" -}}
app.kubernetes.io/name: {{ include "scoring-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "scoring-engine.selectorLabels" -}}
app.kubernetes.io/name: {{ include "scoring-engine.name" . }}
{{- end -}}
