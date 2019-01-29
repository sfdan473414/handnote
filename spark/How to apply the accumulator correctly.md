
说明：  
Spark 版本：`2.0.0.cloudera2`  

在Spark中累加器(`Accumulator`)是作为共享变量来使用的，但是在使用累加器时需要额外注意一些事项。  

* 如何使用累加器?

```scala
val accLong:LongAccumulator= new LongAccumulator
sc.register(accLong,"AccuLong") // val sc:SparkContext
val rdd= sc.parallelize(1 to 10)
val rddMap= rdd.map{
  id=>
    accLong.add(1)
    id+1
}
```

累加器在使用之前必须要进行`register`,从源码的角度来看，`Accumulator`也是一种弱引用，且使用的是`ContectCleaner`来进行回收和清理。因此一定要进行注册。  

累加器的值在Task任务中被更新且一个Excutor上的多线程之间对累加器的操作是线程安全的。在每个Task中只能对累加器进行更新而不能获取累加器的值，累加器的值只能在Driver上获取。  

* 在`transform`RDD中使用时的陷阱？
  
  在Spark中，如果在转换算子中使用累加器，可能会造成累加器的重复更新。我们知道，累加器的更新是在Task中执行的。Spark的Task可能会多次重复执行以至于累加器的值被多次更新。  
  转换算子RDD都是`lazy`模式，只有在遇到Action时根据血统来计算所有依赖的RDD。因此如果多次调用Action，那么累加器的值会多次被更新。  

  ```scala
  val accLong:LongAccumulator= new LongAccumulator
    sc.register(accLong,"AccuLong")
    val rdd= sc.parallelize(1 to 10)
    val rddMap= rdd.map{
      id=>
        accLong.add(1)
        id+1
    }

    println( rddMap.collect().toList)  // 执行collect
    println( rddMap.collect().toList) // 执行collect

    println(accLong.value) // 打印 累加器的值
    // result 20
  ```

* 在算子中可能会引起任务重新执行的动机？
  
  - Spark中的某个任务失败了或者任务执行过慢，那么Spark会重新启动任务
  - 当遇到多个Action操作
  - RDD缓存被清理掉，在重新使用该RDD时会重新计算。