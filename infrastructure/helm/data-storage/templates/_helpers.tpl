{{- define "data-storage.fullname" -}}
{{ include "data-storage.name" . }}
{{- end -}}

{{- define "data-storage.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "data-storage.labels" -}}
app.kubernetes.io/name: {{ include "data-storage.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "data-storage.selectorLabels" -}}
app.kubernetes.io/name: {{ include "data-storage.name" . }}
{{- end -}}
