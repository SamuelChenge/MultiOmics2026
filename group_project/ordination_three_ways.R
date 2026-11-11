# Step 2 of notebook 03: the species table, ordinated three ways.
library(tidyverse)
library(here)
library(microViz)
library(phyloseq)
library(vegan) # PERMANOVA (adonis2) lives here

source(here("R/count_tables.R"))

sample_groups <- read_csv(here("data/my_sample_groups.csv"))
ps_species <- as_counts(table = "microbiome")

# Join the community column (built in notebook 02) onto the sample table.
sd <- as(sample_data(ps_species), "data.frame") |>
  rownames_to_column("sid") |>
  left_join(sample_groups, by = c("sid" = "sample_id")) |>
  column_to_rownames("sid")
sample_data(ps_species) <- sample_data(sd)

# One knob each: transform -> distance -> ordination.
ord_bray    <- ps_species |> tax_transform("identity") |> dist_calc("bray")    |> ord_calc("PCoA")
ord_jaccard <- ps_species |> tax_transform("binary")   |> dist_calc("jaccard") |> ord_calc("PCoA")
ord_clr     <- ps_species |> tax_transform("clr", zero_replace = "halfmin") |> dist_calc("euclidean") |> ord_calc("PCoA")

# Axis titles carry the share of variation each axis holds.
plot_ord <- function(ord, name) {
  eig <- attr(ord, "ord")$CA$eig
  sh  <- round(100 * eig / sum(eig), 1)
  ord_plot(ord, axes = 1:2, color = "community") +
    labs(title = name,
         x = sprintf("Axis 1 (%s%%)", sh[1]),
         y = sprintf("Axis 2 (%s%%)", sh[2]))
}

scree_shares <- function(ord, name) {
  eig <- attr(ord, "ord")$CA$eig[1:8]
  tibble(distance = name, axis = seq_along(eig), share = eig / sum(eig))
}

scree <- bind_rows(
  scree_shares(ord_bray, "Bray-Curtis"),
  scree_shares(ord_jaccard, "Jaccard"),
  scree_shares(ord_clr, "CLR + Euclidean")
)

p <- patchwork::wrap_plots(
  plot_ord(ord_bray, "Bray-Curtis"),
  plot_ord(ord_jaccard, "Jaccard"),
  plot_ord(ord_clr, "CLR + Euclidean"),
  ncol = 3
) / ggplot(scree, aes(axis, share)) +
  geom_col(fill = "grey40") +
  facet_wrap(~ distance) +
  labs(title = "Scree: share of variation held by the first 8 axes",
       x = "Axis", y = "Share of variation") +
  theme_bw()

ggsave(here("group_project", "ordination_three_ways.png"), p,
       width = 13, height = 6, dpi = 150)

# Does community explain more or less depending on the distance? (the argument)
cat("\n--- PERMANOVA: community ~ R2 and p, on each distance ---\n")
perm <- function(ord, name) {
  meta <- as(sample_data(ps_species), "data.frame")
  ad <- adonis2(attr(ord, "dist") ~ community, data = meta, permutations = 999)
  tibble(distance = name, R2 = round(100 * ad$R2[1], 1), p = ad$`Pr(>F)`[1])
}
bind_rows(perm(ord_bray, "Bray-Curtis"), perm(ord_jaccard, "Jaccard"), perm(ord_clr, "CLR + Euclidean")) |>
  print()

# A few sanity numbers the user can check themselves.
cat("\n--- checks ---\n")
cat("samples plotted:", nrow(sample_data(ps_species)), "\n")
cat("missing community:", sum(is.na(sample_data(ps_species)$community)), "\n")
tab <- otu_table(ps_species)@.Data
cat("share of cells that are zero:", round(100 * mean(tab == 0), 1), "%\n")
