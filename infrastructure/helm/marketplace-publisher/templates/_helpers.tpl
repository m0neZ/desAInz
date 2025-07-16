{{- define "marketplace-publisher.fullname" -}}
{{ include "marketplace-publisher.name" . }}
{{- end -}}

{{- define "marketplace-publisher.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "marketplace-publisher.labels" -}}
app.kubernetes.io/name: {{ include "marketplace-publisher.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "marketplace-publisher.selectorLabels" -}}
app.kubernetes.io/name: {{ include "marketplace-publisher.name" . }}
{{- end -}}
