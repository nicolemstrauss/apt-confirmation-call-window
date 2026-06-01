variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "bamboo-file-exchange"
}

variable "template_key" {
  description = "S3 key for the Excel template file"
  default     = "templates/practice_time_window_template.xlsx"
}
