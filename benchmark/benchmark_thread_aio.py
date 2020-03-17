import asyncio

import tracemalloc
import os
import time

from caio.thread_aio_asyncio import AsyncioContext


loop = asyncio.get_event_loop()


chunk_size = 512 * 1024
context_max_requests = 16


async def read_file(ctx: AsyncioContext, file_id):
    offset = 0
    fname = f"data/{file_id}.bin"
    file_size = os.stat(fname).st_size

    with open(fname, "rb") as fp:
        fd = fp.fileno()

        c = 0
        while offset < file_size:
            await ctx.read(chunk_size, fd, offset)
            offset += chunk_size
            c += 1

    return c


async def timer(future):
    await asyncio.sleep(0)
    delta = time.monotonic()
    return await future, time.monotonic() - delta


async def main():
    print("files   nr      min   madian      max   op/s    total  #ops chunk")
    tracemalloc.start()

    snapshot1 = tracemalloc.take_snapshot()

    for generation in range(1, 129):
        context = AsyncioContext(context_max_requests)

        futures = []

        for file_id in range(generation):
            futures.append(read_file(context, file_id))

        stat = []
        total = -time.monotonic()
        nops = 0

        for ops, delta in await asyncio.gather(*map(timer, futures)):
            stat.append(delta)
            nops += ops

        total += time.monotonic()

        stat = sorted(stat)

        ops_sec = nops / total

        dmin = stat[0]
        dmedian = stat[int(len(stat) / 2)]
        dmax = stat[-1]

        print(
            "%5d %4d %2.6f %2.6f %2.6f %6d %-3.6f %5d %d"
            % (
                generation,
                context_max_requests,
                dmin,
                dmedian,
                dmax,
                ops_sec,
                total,
                nops,
                chunk_size,
            )
        )

        await context.close()

        snapshot2 = tracemalloc.take_snapshot()

        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        # print("[ Top 10 differences ]")
        # for stat in top_stats[:10]:
        #     print(stat)



if __name__ == "__main__":
    loop.run_until_complete(main())
