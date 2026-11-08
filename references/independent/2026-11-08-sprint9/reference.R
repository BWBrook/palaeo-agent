args <- commandArgs(trailingOnly = TRUE); stopifnot(length(args) == 1L); d <- normalizePath(args[[1L]])
cp_bounds <- function(b, B) c(if (b == 0) 0 else stats::qbeta(.025, b, B-b+1), if (b == B) 1 else stats::qbeta(.975, b+1, B-b))
api <- read.csv(file.path(d,'api.csv'), stringsAsFactors=FALSE)
api$ref_p <- (api$b+1)/(api$B+1)
api$ref_lo <- api$ref_hi <- api$ref_p_holm <- api$ref_envelope_lo <- api$ref_envelope_hi <- NA_real_
for (i in seq_len(nrow(api))) {
 v <- cp_bounds(api$b[i],api$B[i]);api$ref_lo[i] <- v[1];api$ref_hi[i] <- v[2]
}
for (run in unique(api$run)) {
 z <- which(api$run == run)
 api$ref_p_holm[z] <- stats::p.adjust(api$ref_p[z],method='holm')
 api$ref_envelope_lo[z] <- stats::p.adjust(api$ref_lo[z],method='holm')
 api$ref_envelope_hi[z] <- stats::p.adjust(api$ref_hi[z],method='holm')
}
api$ref_unresolved <- as.integer(api$ref_lo <= .05 & .05 <= api$ref_hi)
api$ref_envelope_unresolved <- as.integer(api$ref_envelope_lo <= .05 & .05 <= api$ref_envelope_hi)
edge <- read.csv(file.path(d,'edge.csv'))
edge$ref_p_holm <- edge$ref_envelope_lo <- edge$ref_envelope_hi <- NA_real_
for (run in unique(edge$run)) {
 z <- which(edge$run == run)
 edge$ref_p_holm[z] <- stats::p.adjust(edge$p[z],method='holm')
 edge$ref_envelope_lo[z] <- stats::p.adjust(edge$lo[z],method='holm')
 edge$ref_envelope_hi[z] <- stats::p.adjust(edge$hi[z],method='holm')
}
edge$ref_envelope_unresolved <- as.integer(edge$ref_envelope_lo <= .05 & .05 <= edge$ref_envelope_hi)
cp <- read.csv(file.path(d,'cp.csv'))
refs <- t(vapply(seq_len(nrow(cp)),function(i) cp_bounds(cp$b[i],cp$B[i]),numeric(2)))
cp$ref_lo <- refs[,1];cp$ref_hi <- refs[,2]
api_fields <- c('p','p_holm','lo','hi','envelope_lo','envelope_hi','unresolved','envelope_unresolved')
edge_fields <- c('p_holm','envelope_lo','envelope_hi','envelope_unresolved')
check <- function(x,fields,label) {
 errs <- unlist(lapply(fields,function(f) abs(x[[f]]-x[[paste0('ref_',f)]])))
 data.frame(check=label,fields=length(errs),max_abs_error=max(errs),tolerance=1e-12,passed=all(errs<=1e-12))
}
summary <- rbind(check(api,api_fields,'public_API'),check(edge,edge_fields,'edge_vectors'),check(cp,c('lo','hi'),'CP_endpoints'))
a <- edge[edge$run=='edge',];b <- edge[edge$run=='edge_permuted',];a<-a[order(a$item),];b<-b[order(b$item),]
stopifnot(identical(a$p_holm,b$p_holm),identical(a$envelope_lo,b$envelope_lo),identical(a$envelope_hi,b$envelope_hi),identical(a$envelope_unresolved,b$envelope_unresolved))
write.csv(api,file.path(d,'api-r-reference.csv'),row.names=FALSE)
write.csv(edge,file.path(d,'edge-r-reference.csv'),row.names=FALSE)
write.csv(cp,file.path(d,'cp-r-reference.csv'),row.names=FALSE)
write.csv(summary,file.path(d,'summary.csv'),row.names=FALSE)
print(summary,row.names=FALSE)
cat('Fixed-vector pair-order permutation: exact pass\n')
cat('Exact envelope lower=.05 boundary flags:',edge$envelope_unresolved[edge$envelope_lo==.05],'\n')
cat(R.version.string,'\n')
stopifnot(all(summary$passed))
