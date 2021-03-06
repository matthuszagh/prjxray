#!/usr/bin/env python3

from timfuz import Benchmark, loadc_Ads_bs, load_sub, Ads2bounds, corners2csv, corner_s2i


def gen_flat(fns_in, sub_json, corner=None):
    Ads, bs = loadc_Ads_bs(fns_in, ico=True)
    bounds = Ads2bounds(Ads, bs)
    # Elements with zero delay assigned due to sub group
    group_zeros = set()
    # Elements with a concrete delay
    nonzeros = set()

    if corner:
        zero_row = [None, None, None, None]
        zero_row[corner_s2i[corner]] = 0
    else:
        zero_row = None

    for bound_name, bound_bs in bounds.items():
        sub = sub_json['subs'].get(bound_name, None)
        if bound_name in sub_json['zero_names']:
            if zero_row:
                yield bound_name, 0
        elif sub:
            #print('sub', sub)
            # put entire delay into pivot
            pivot = sub_json['pivots'][bound_name]
            assert pivot not in group_zeros
            nonzeros.add(pivot)
            non_pivot = set(sub.keys() - set([pivot]))
            #for name in non_pivot:
            #    assert name not in nonzeros, (pivot, name, nonzeros)
            group_zeros.update(non_pivot)
            #print('yield PIVOT', pivot)
            yield pivot, bound_bs
        else:
            nonzeros.add(bound_name)
            yield bound_name, bound_bs
    # non-pivots can appear multiple times, but they should always be zero
    # however, due to substitution limitations, just warn
    violations = group_zeros.intersection(nonzeros)
    if len(violations):
        print('WARNING: %s non-0 non-pivot' % (len(violations)))

    # XXX: how to best handle these?
    # should they be fixed 0?
    if zero_row:
        # ZERO names should always be zero
        #print('ZEROs: %u' % len(sub_json['zero_names']))
        for zero in sub_json['zero_names']:
            #print('yield ZERO', zero)
            yield zero, zero_row

        real_zeros = group_zeros - violations
        print(
            'Zero candidates: %u w/ %u non-pivot conflicts => %u zeros as solved'
            % (len(group_zeros), len(violations), len(real_zeros)))
        # Only yield elements not already yielded
        for zero in real_zeros:
            #print('yield solve-0', zero)
            yield zero, zero_row


def run(fns_in, fnout, sub_json, corner=None, verbose=False):
    with open(fnout, 'w') as fout:
        fout.write('ico,fast_max fast_min slow_max slow_min,rows...\n')
        for name, corners in sorted(list(gen_flat(fns_in, sub_json,
                                                  corner=corner))):
            row_ico = 1
            items = [str(row_ico), corners2csv(corners)]
            items.append('%u %s' % (1, name))
            fout.write(','.join(items) + '\n')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Substitute .csv to ungroup correlated variables')

    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--sub-csv', help='')
    parser.add_argument(
        '--sub-json',
        required=True,
        help='Group substitutions to make fully ranked')
    parser.add_argument('--corner', default=None, help='')
    parser.add_argument('--out', default=None, help='output timing delay .csv')
    parser.add_argument(
        'fns_in',
        nargs='+',
        help='input timing delay .csv (NOTE: must be single column)')
    args = parser.parse_args()
    # Store options in dict to ease passing through functions
    bench = Benchmark()

    sub_json = load_sub(args.sub_json)

    try:
        run(
            args.fns_in,
            args.out,
            sub_json=sub_json,
            verbose=args.verbose,
            corner=args.corner)
    finally:
        print('Exiting after %s' % bench)


if __name__ == '__main__':
    main()
