from main import main


def profile_main():
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        main()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats("fast_main.prof")


if __name__ == "__main__":

    # about a 3.293/32.934 sec ratio from fast vs deep copy approach

    profile_main()
