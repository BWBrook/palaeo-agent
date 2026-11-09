args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
here <- args[1]
work <- args[2]
source <- read.csv(file.path(here, "source/STable1_2DLimpets.csv"), check.names = FALSE)
api <- read.csv(file.path(here, "bootstrap-amended.csv"))
inference <- read.csv(file.path(here, "inference-amended.csv"))
indices <- as.matrix(read.csv(file.path(work, "indices.csv"), header = FALSE))
stopifnot(nrow(indices) == 9999L, ncol(indices) == 136L,
          nrow(source) == 136L, !anyDuplicated(source$ObjectID), nrow(api) == 9999L)
columns <- list(caliper_log = c("Length_Caliper_mm", "Width_Caliper_mm"),
                automorph_log = c("MajorAxisLength_AutoMorph_mm", "MinorAxisLength_AutoMorph_mm"))
checks <- list()
add <- function(field, r_value, api_value) {
  stopifnot(length(r_value) == length(api_value), all(is.finite(r_value)), all(is.finite(api_value)))
  checks[[length(checks) + 1L]] <<- data.frame(field = field, r_value = r_value, api_value = api_value,
    absolute_difference = abs(r_value - api_value),
    passed = abs(r_value - api_value) <= 1e-10 + 1e-10 * abs(api_value))
}
slope <- function(x, y) sign(cov(x, y)) * sd(y) / sd(x)
replicates <- list()
observed <- c()
for (id in names(columns)) {
  x <- log10(source[[columns[[id]][1]]])
  y <- log10(source[[columns[[id]][2]]])
  n <- length(x)
  expected <- inference[inference$analysis_id == id, ]
  r <- cor(x, y)
  magnitude <- sd(y) / sd(x)
  B <- (1-r^2) * qf(expected$confidence, 1, n-2) / (n-2)
  H <- sqrt(1+B) + sqrt(B)
  rr <- cor(y - expected$null_magnitude*x, y + expected$null_magnitude*x)
  magnitude_p <- 2*pt(abs(rr * sqrt((n-2)/(1-rr^2))), n-2, lower.tail = FALSE)
  direction_p <- 2*pt(abs(r * sqrt((n-2)/(1-r^2))), n-2, lower.tail = FALSE)
  values <- c(magnitude = magnitude, low = magnitude/H, high = magnitude*H,
              magnitude_p = magnitude_p, direction_p = direction_p)
  for (field in names(values)) add(paste(id, field, sep = ":"), values[[field]], expected[[field]])
  observed[id] <- slope(x, y)
  replicates[[id]] <- vapply(seq_len(nrow(indices)), function(i) slope(x[indices[i, ]], y[indices[i, ]]), numeric(1))
}
a <- replicates$caliper_log
b <- replicates$automorph_log
d <- b-a
add("bootstrap:slope_a", a, api$slope_a)
add("bootstrap:slope_b", b, api$slope_b)
add("bootstrap:difference", d, api$difference)
summary_api <- read.csv(file.path(work, "summary-api.csv"), stringsAsFactors = FALSE)
q <- c(0.025000000000000022, 0.975)
ci <- quantile(d, probs = q, type = 7, names = FALSE)
ordered <- sort(d)
ranks <- lapply(q, function(v) c(qbinom(0.005, 9999, v), qbinom(0.995, 9999, v)+1))
summary_r <- c(difference = unname(observed[2] - observed[1]), standard_error = sd(d),
              interval_low = ci[1], interval_high = ci[2],
              lower_rank_low = ranks[[1]][1], lower_rank_high = ranks[[1]][2],
              upper_rank_low = ranks[[2]][1], upper_rank_high = ranks[[2]][2],
              lower_band_low = ordered[ranks[[1]][1]], lower_band_high = ordered[ranks[[1]][2]],
              upper_band_low = ordered[ranks[[2]][1]], upper_band_high = ordered[ranks[[2]][2]],
              sign_changes_a = sum(sign(a) != sign(observed[1])), sign_changes_b = sum(sign(b) != sign(observed[2])))
stopifnot(setequal(names(summary_r), summary_api$field))
for (field in names(summary_r)) add(paste0("summary:", field), summary_r[[field]], summary_api$value[summary_api$field == field])
checks <- do.call(rbind, checks)
options(digits = 17)
write.csv(checks, file.path(work, "comparisons.csv"), row.names = FALSE)
write.csv(data.frame(status = if (all(checks$passed)) "passed" else "failed", r_version = R.version.string,
                     quantities = nrow(checks), max_absolute_difference = max(checks$absolute_difference)),
          file.path(work, "receipt.csv"), row.names = FALSE)
stopifnot(all(checks$passed))
cat("Passed", nrow(checks), "independent base-R comparisons; max absolute difference", max(checks$absolute_difference), "\n")
