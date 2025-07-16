{{- define "orchestrator.fullname" -}}
{{ include "orchestrator.name" . }}
{{- end -}}

{{- define "orchestrator.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "orchestrator.labels" -}}
app.kubernetes.io/name: {{ include "orchestrator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "orchestrator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "orchestrator.name" . }}
{{- end -}}
