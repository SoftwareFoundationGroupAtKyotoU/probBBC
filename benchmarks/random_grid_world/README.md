`random_grid_world`
===================

This directory contains `random_grid_world` benchmark.

Model generation
----------------

If you want to re-generate the models, please run the following. The while-loop is required because we remove a model to re-generate it if it is too hard to satisfy the given property.

```sh
while ! make -j4; do
    true;
done
```

