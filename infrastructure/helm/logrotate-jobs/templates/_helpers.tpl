{{- define "logrotate-jobs.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "logrotate-jobs.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if .Values.fullnameOverride -}}
{{- $name = .Values.fullnameOverride -}}
{{- end -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "logrotate-jobs.labels" -}}
helm.sh/chart: {{ include "logrotate-jobs.chart" . }}
{{ include "logrotate-jobs.selectorLabels" . }}
{{- if .Chart.AppVersion -}}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "logrotate-jobs.selectorLabels" -}}
app.kubernetes.io/name: {{ include "logrotate-jobs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "logrotate-jobs.chart" -}}
{{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}
