"""Draw frozen pollen profiles and native zonation fields without refitting."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    checked = json.loads((HERE / 'reproduction-check.json').read_text())
    digest = next(item['sha256'] for item in checked['exports'] if item['file'] == 'results.json')
    assert hashlib.sha256((HERE / 'results.json').read_bytes()).hexdigest() == digest
    data = json.loads((HERE / 'results.json').read_text())
    context = json.loads((HERE / 'context.json').read_text())
    tables = HERE / 'tables'
    tables.mkdir(exist_ok=True)
    with (tables / 'broken-stick.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['analysis_id', 'rank', 'zones', 'gain', 'expected', 'exceeds'],
                                lineterminator='\n')
        writer.writeheader()
        writer.writerows({'analysis_id': name, **row}
                         for name, result in data['coniss'].items() for row in result['broken_stick'])
    primary = data['coniss']['archive_hellinger']
    depths = primary['positions']
    plot = data['plot']
    assert plot['sample_ids'] == primary['sample_ids']
    fig, axes = plt.subplots(1, 12, figsize=(17, 10), sharey=True,
                             gridspec_kw={'width_ratios': [1] * 7 + [.44] * 4 + [1.6]})
    fig.subplots_adjust(left=.055, right=.985, bottom=.10, top=.76, wspace=.24)
    for ax, taxon in zip(axes[:7], context['plot_taxa']):
        column = plot['taxon_ids'].index(taxon)
        percent = [100 * row[column] for row in plot['transformed_matrix']]
        ax.fill_betweenx(depths, 0, percent, color='#478875', alpha=.70)
        ax.plot(percent, depths, color='#245b4b', linewidth=.8)
        ax.set_xlim(0, max(percent) * 1.06)
        ax.set_title(taxon.replace(' ', '\n', 1), fontsize=10, rotation=58,
                     ha='left', va='bottom', pad=12, fontstyle='italic')
        ax.set_xlabel('%', fontsize=9)
        ax.locator_params(axis='x', nbins=3)
        for boundary in primary['boundaries']:
            if boundary['split_rank'] < primary['retention']['selected_zones']:
                ax.axhline((boundary['left_position'] + boundary['right_position']) / 2,
                           color='#666666', linestyle=':', linewidth=.7)
    names = ['archive_hellinger', 'repaired_hellinger', 'archive_relative', 'repaired_relative']
    titles = ['Hellinger\narchive', 'Hellinger\nrepair', 'Relative\narchive', 'Relative\nrepair']
    palette = ['#d2e8d4', '#f1d59b', '#b6d4e7', '#dfc3db', '#c9c8e3', '#ecc4ad']
    for ax, name, title in zip(axes[7:11], names, titles):
        result = data['coniss'][name]
        gaps = sorted((b['left_position'] + b['right_position']) / 2
                      for b in result['boundaries']
                      if b['split_rank'] < result['retention']['selected_zones'])
        edges = [depths[0], *gaps, depths[-1]]
        for zone, lo, hi in zip(result['zones'], edges[:-1], edges[1:]):
            ax.axhspan(lo, hi, color=palette[zone['label'] - 1], ec='white', linewidth=.8)
            ax.text(.5, (lo + hi) / 2, str(zone['label']), ha='center', va='center', fontsize=9)
        ax.set_title(title, fontsize=9, pad=12)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_xlabel(f"k = {result['retention']['selected_zones']}", fontsize=9)
    dendro = axes[-1]
    nodes = {(sample, sample): (0, depth)
             for sample, depth in zip(primary['sample_ids'], depths)}
    for merge in primary['merges']:
        left = nodes.pop((merge['left_first_id'], merge['left_last_id']))
        right = nodes.pop((merge['right_first_id'], merge['right_last_id']))
        height = merge['cumulative']
        dendro.plot([left[0], height, height, right[0]],
                    [left[1], left[1], right[1], right[1]], color='#34445a', linewidth=.7)
        nodes[(merge['left_first_id'], merge['right_last_id'])] = (height, (left[1] + right[1]) / 2)
    dendro.set_title('Primary hierarchy', fontsize=10, pad=12)
    dendro.set_xlabel('Cumulative SS', fontsize=9)
    dendro.set_xlim(0, primary['total_dispersion'] * 1.02)
    dendro.locator_params(axis='x', nbins=3)
    for ax in axes:
        ax.set_ylim(depths[-1] + 2, depths[0] - 2)
        ax.tick_params(labelsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_ylabel('Archive depth (cm)', fontsize=11)
    axes[0].set_yticks(np.arange(100, 426, 25))
    fig.suptitle('Lake Selina: count repair preserves the selected zones; taxon weighting changes them',
                 fontsize=15, x=.055, ha='left', y=.97)
    fig.text(.055, .922, '72 levels · 60 dryland pollen categories · equal sample weights · depth only', fontsize=11)
    fig.text(.055, .035, 'Profiles: archived dryland percentages. Zone lines lie at gap midpoints for drawing only; '
             'boundary tables retain both observed depths.\nRepair: inferred 72 Lagarostrobos grains at 220 cm. '
             'Hierarchy uses cumulative within-zone SS, not individual merge costs.', fontsize=9)
    target = HERE / 'figures'
    target.mkdir(exist_ok=True)
    fig.savefig(target / 'zonation.png', dpi=150)
    fig.savefig(target / 'zonation.pdf', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)


if __name__ == '__main__':
    main()
