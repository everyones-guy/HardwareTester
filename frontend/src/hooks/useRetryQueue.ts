// /src/hooks/useRetryQueue.ts
import { useRef } from "react";

type RetryTask = {
    fn: () => Promise<any>;
    resolve: (val: any) => void;
    reject: (err: any) => void;
};

const useRetryQueue = (concurrency = 1) => {
    const queue = useRef<RetryTask[]>([]);
    const running = useRef(0);

    const runNext = () => {
        if (running.current >= concurrency || queue.current.length === 0) return;

        const { fn, resolve, reject } = queue.current.shift()!;
        running.current++;

        fn()
            .then(resolve)
            .catch(reject)
            .finally(() => {
                running.current--;
                runNext();
            });
    };

    const enqueue = (fn: () => Promise<any>) => {
        return new Promise((resolve, reject) => {
            queue.current.push({ fn, resolve, reject });
            runNext();
        });
    };

    return { enqueue };
};

export default useRetryQueue;
