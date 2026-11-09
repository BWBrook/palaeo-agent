args <- commandArgs(trailingOnly = TRUE)
script <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE))
here <- dirname(script)
paths <- if (length(args)) args else file.path(here, c(
  "api-pairs.csv", "api-scalars.csv", "r-reference.csv", "r-check.json"))
stopifnot(length(paths) == 4L)

pairs <- read.csv(paths[1], stringsAsFactors = FALSE, check.names = FALSE)
scalars <- read.csv(paths[2], stringsAsFactors = FALSE, check.names = FALSE)
fields <- c("n", "mean_x", "mean_y", "sd_x", "sd_y", "correlation", "slope",
            "intercept", "vertical_residual_rmse")
stopifnot(all(c("analysis_id", "sample_id", "x_raw", "y_raw", "x", "y", "residual") %in% names(pairs)),
          all(c("analysis_id", fields) %in% names(scalars)),
          identical(sort(unique(pairs$analysis_id)), sort(scalars$analysis_id)),
          !anyDuplicated(scalars$analysis_id))

checks <- list()
add_check <- function(id, sample_id, field, value, api) {
  stopifnot(length(value) == length(api), all(is.finite(value)), all(is.finite(api)))
  difference <- abs(value - api)
  allowed <- 1e-10 + 1e-10 * abs(api)
  checks[[length(checks) + 1L]] <<- data.frame(
    analysis_id = id, sample_id = sample_id, field = field, r_value = value,
    api_value = api, absolute_difference = difference,
    allowed_difference = allowed, passed = difference <= allowed,
    stringsAsFactors = FALSE)
}

for (id in scalars$analysis_id) {
  p <- pairs[pairs$analysis_id == id, , drop = FALSE]
  expected <- scalars[scalars$analysis_id == id, , drop = FALSE]
  stopifnot(nrow(p) >= 2L, !anyDuplicated(p$sample_id), all(p$x_raw > 0), all(p$y_raw > 0))
  x <- log10(p$x_raw)
  y <- log10(p$y_raw)
  r <- cor(x, y)
  slope <- sign(r) * sd(y) / sd(x)
  intercept <- mean(y) - slope * mean(x)
  residual <- y - (intercept + slope * x)
  values <- c(n = length(x), mean_x = mean(x), mean_y = mean(y),
              sd_x = sd(x), sd_y = sd(y), correlation = r, slope = slope,
              intercept = intercept, vertical_residual_rmse = sqrt(mean(residual^2)))
  for (field in fields) add_check(id, "", field, values[[field]], expected[[field]])
  add_check(id, p$sample_id, "x", x, p$x)
  add_check(id, p$sample_id, "y", y, p$y)
  add_check(id, p$sample_id, "residual", residual, p$residual)
}

out <- do.call(rbind, checks)
options(digits = 17)
write.csv(out, paths[3], row.names = FALSE, na = "")
quote_json <- function(value) encodeString(value, quote = '"')
status <- if (all(out$passed)) "passed" else "failed"
hashes <- tools::md5sum(paths[1:2])
receipt <- c(
  "{",
  paste0('  "status": ', quote_json(status), ','),
  paste0('  "r_version": ', quote_json(R.version.string), ','),
  '  "command": "Rscript --vanilla analyses/fossil-limpets/reference.R",',
  '  "scope": "Independent base-R arithmetic on the saved API pairs; no inference or new fit selection",',
  '  "transform": "log10 applied independently to x_raw and y_raw",',
  '  "absolute_tolerance": 1e-10,',
  '  "relative_tolerance": 1e-10,',
  '  "criterion": "abs(R - API) <= 1e-10 + 1e-10 * abs(API)",',
  paste0('  "fits_checked": ', nrow(scalars), ','),
  paste0('  "scalar_quantities_checked": ', nrow(scalars) * length(fields), ','),
  paste0('  "specimen_quantities_checked": ', nrow(out) - nrow(scalars) * length(fields), ','),
  paste0('  "total_quantities_checked": ', nrow(out), ','),
  paste0('  "max_absolute_difference": ', format(max(out$absolute_difference), scientific = TRUE, digits = 17), ','),
  '  "inputs": [',
  paste0('    {"file": ', quote_json(basename(paths[1])), ', "md5": ', quote_json(unname(hashes[1])), '},'),
  paste0('    {"file": ', quote_json(basename(paths[2])), ', "md5": ', quote_json(unname(hashes[2])), '}'),
  "  ]",
  "}")
writeLines(receipt, paths[4])
cat(status, ":", nrow(out), "quantities; max absolute difference",
    format(max(out$absolute_difference), scientific = TRUE, digits = 17), "\n")
if (!all(out$passed)) quit(status = 1L)
