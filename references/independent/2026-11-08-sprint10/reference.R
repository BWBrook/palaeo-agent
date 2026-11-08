args <- commandArgs(trailingOnly = TRUE); stopifnot(length(args) == 1L)
d <- normalizePath(args[[1L]])
repo <- normalizePath(file.path(d, '../../..'))
audit_libs <- list.dirs(file.path(repo, "references/r/renv/library"), recursive=TRUE)
audit_libs <- audit_libs[basename(audit_libs)==R.version$platform & dir.exists(file.path(audit_libs,"vegan"))]
.libPaths(c(audit_libs,.libPaths()))
suppressPackageStartupMessages(library(vegan))
a <- read.csv(file.path(d,'api.csv'),stringsAsFactors=FALSE)
meta <- read.csv(file.path(d,'metadata.csv'),stringsAsFactors=FALSE);meta$group<-factor(meta$group)
inputs <- lapply(c('percentage','proportion','row_scaled','count_smoke'),function(n) as.matrix(read.delim(file.path(d,paste0(n,'.tsv')),row.names=1,check.names=FALSE)))
names(inputs)<-c('percentage','proportion','row_scaled','count_smoke')
a$reference <- NA_real_
for (variant in names(inputs)) {
 x<-inputs[[variant]];div<-data.frame(sample=rownames(x),richness=specnumber(x),shannon=diversity(x,index='shannon'),simpson=diversity(x,index='simpson'),weight_sum=rowSums(x),total=rowSums(x),row.names=rownames(x))
 for (transform in c('none','relative_abundance')) {
  for (distance in c('braycurtis','jaccard')) {
   if(distance=='jaccard' && transform!='none') next
   z<-if(transform=='relative_abundance') decostand(x,method='total') else x
   dd<-vegdist(z,method=if(distance=='braycurtis') 'bray' else 'jaccard',binary=distance=='jaccard');dm<-as.matrix(dd)
   fit<-adonis2(dd~group,data=meta,permutations=0)
   ix<-which(a$variant==variant & a$transform==transform & a$distance==distance)
   for(i in ix) {
    metric<-a$metric[i]
    a$reference[i]<-if(metric=='distance') dm[a$item1[i],a$item2[i]] else if(metric=='pseudo_f') fit$F[1] else if(metric=='r_squared') fit$R2[1] else div[a$item1[i],metric]
   }
  }
 }
}
a$error<-abs(a$value-a$reference);a$tolerance<-1e-10*(1+abs(a$reference));a$passed<-a$error<=a$tolerance
summary<-aggregate(error~method+metric,data=a,max);print(summary,row.names=FALSE)
cat('Fields:',nrow(a),'passed:',sum(a$passed),'max abs:',max(a$error),'\n')
write.csv(a,file.path(d,'r-reference.csv'),row.names=FALSE);write.csv(summary,file.path(d,'summary.csv'),row.names=FALSE)
# Metamorphic checks compare API-produced quantities, not a third implementation.
key<-function(x) paste(x$method,x$transform,x$distance,x$metric,x$item1,x$item2,sep='|')
b<-a[a$variant=='percentage' & !a$metric%in%c('total','weight_sum'),];p<-a[a$variant=='proportion' & !a$metric%in%c('total','weight_sum'),];s<-a[a$variant=='row_scaled' & !a$metric%in%c('total','weight_sum'),]
p<-p[match(key(b),key(p)),];s<-s[match(key(b),key(s)),]
common<-max(abs(b$value-p$value));closed<-max(abs(b$value[b$transform=='relative_abundance']-s$value[b$transform=='relative_abundance']));raw<-max(abs(b$value[b$metric=='distance' & b$transform=='none' & b$distance=='braycurtis']-s$value[b$metric=='distance' & b$transform=='none' & b$distance=='braycurtis']))
cat('Commonfactor maxdiff:',common,'row-specific closure maxdiff:',closed,'row-specific raw BC maxdiff:',raw,'\n')
write.csv(data.frame(commonfactor_maxdiff=common,rowspecific_closed_maxdiff=closed,rowspecific_raw_BC_maxdiff=raw),file.path(d,'invariance.csv'),row.names=FALSE)
cat(R.version.string,'vegan',as.character(packageVersion('vegan')),'\n')
stopifnot(all(a$passed),common<=1e-10,closed<=1e-10,raw>1e-3)
