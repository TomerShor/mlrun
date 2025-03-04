(function_runtimes)=
# Kinds of functions (runtimes)

When you create an MLRun function you need to specify a runtime kind (e.g. `kind='job'`). Each runtime supports 
its own specific attributes (e.g. Jars for Spark, triggers for Nuclio, auto-scaling for Dask, etc.).

MLRun supports real-time and batch runtimes.

Real-time runtimes:
* **{ref}`nuclio <nuclio-real-time-functions>`** - real-time serverless functions over Nuclio
* **{ref}`serving <serving-function>`** - deploy models and higher-level real-time Graph (DAG) over one or more Nuclio functions
* **{ref}`application <application>`** &mdash; run an image (application) on top of your deployed model

Batch runtimes:
* **handler** &mdash; execute python handler (used automatically in notebooks or for debug)
* **local** &mdash; execute a Python or shell program 
* **{ref}`job <job-function>`** &mdash; run the code in a Kubernetes Pod
* **{ref}`dask <dask-overview>`** &mdash; run the code as a Dask Distributed job (over Kubernetes)
* **{ref}`databricks <databricks>`** &mdash; run code on Databricks cluster (python scripts, Spark etc)
* **{ref}`mpijob <horovod>`** &mdash; run distributed jobs and Horovod over the MPI job operator, used mainly for deep learning jobs 
* **{ref}`spark <spark-operator>`** &mdash; run the job as a Spark job (using Spark Kubernetes Operator)
* **[remote-spark](../feature-store/using-spark-engine.md#remote-spark-ingestion-example)** &mdash; run the job on a remote Spark service/cluster (e.g. Iguazio Spark service)

**Common attributes for Kubernetes-based functions** 

All the Kubernetes-based runtimes (Application, Job, Dask, Spark, Nuclio, MPIJob, Serving) support a common 
set of spec attributes and methods for setting the pods:

function.spec attributes (similar to k8s pod spec attributes):
* volumes
* volume_mounts
* env
* resources
* replicas
* image_pull_policy
* service_account
* image_pull_secret

common function methods:
* set_env(name, value)
* set_envs(env_vars)
* gpus(gpus, gpu_type)
* set_env_from_secret(name, secret, secret_key)

The limits methods are different for Spark and Dask:
- Spark
   - with_driver_limits(mem, cpu, gpu_type)
   - with_executor_limits(mem, cpu, gpu_type)
- Dask
   - with_scheduler_limits(mem, cpu, gpu_type)
   - with_worker_limits(mem, cpu, gpu_type)

**In this section**
```{toctree}
:maxdepth: 1

../runtimes/job-function
../runtimes/serving-function
../runtimes/application
../runtimes/dask-overview
../runtimes/databricks
../runtimes/horovod
../runtimes/spark-operator
../concepts/nuclio-real-time-functions
```
