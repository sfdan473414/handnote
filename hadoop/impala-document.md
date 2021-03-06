
impala 可以直接地对存储在HDFS、HBase、S3等Hadoop数据提供了一种快速的、可交互式的SQL查询。  

impala 的优势：

* 类SQL语句，可以让数据科学家和分析师直接的使用
* 集群环境中支持分布式查询

impala的组件：

* 客户端`--` 主要的客户端有Hue、ODBC、JDBC、Impala Shell。
* Hive元数据`--`存储了Impala可用的数据信息。这些数据信息可以让Impala什么数据库可以使用以及数据库的结构信息。当对表格进行操作如创建、删除、修改、加载数据等时，相关改动的元数据被自动广播到Impala节点。由此可见Impala与Hive共用源数据库.
* Impala`--` Impala运行在DataNode上，主要是协调和执行查询。Impala的每个实例都可以从客户端接受、计划、协调查询。查询被分布到Impala节点上，这些节点可以看作是Worker执行并行查询。
* HBase and HDFS `--` 存储数据

impala 执行查询的大致过程：

>  1. 用户程序通过ODBC或者JDBC发送SQL查询，用户程序可能需要连接到集群中的任何一个`impalad`，对于此次查询，被连接`impalad`会成为一个协调服务。  
>  2. Impala解析和分析发送的查询语句，确定什么样的任务需要在集群中的`impalad`实例上执行，并通过优化执行计划以获取更高效的查询。  
>  3. 本地`impalad`实例访问HDFS和HBase等服务以提供数据。
>  4. 每个`impalad`都会将数据返回给协调`impalad`，协调的`impalad`会将这些结果发送给客户端。  

# Impala 服务组件

Impala服务组件包含了不同的后台进程，这些后台进程运行在集群中特定的主机上。主要的服务进程有：

## Impala Daemon

Impala 守护进程是Impala组件服务中的核心进程，该服务进程运行在集群中的每个DataNode上，后台的进程名显示为 `impalad`。它主要功能有：读取数据文件、写入数据文件、接收从`impala-shell`、`Hue`、`JDBC`、`ODBC`客户端传输过来的查询、并行化查询并在集群中分配任务、向中心协调服务节点(本质上是一个`impalad`进程)传输中间的查询结果等。  

你可以向任何一个运行了Impala守护进程的DataNode提交一个查询，对于此次查询这个守护进程的实例被称作为一个`coordinator node`.其他的守护进程节点向这个`coordinator node`传输部分数据结果，最终在`coordinator node`上对结果进行了重构形成最终的查询结果集。当通过`impala-shell`命令行运行具有功能性的实验(非生产环境下)时，为了方便你可能总是连接同一个Impala守护进程.对于运行生产工作负载的集群，可以使用JDBC或ODBC接口以循环方式将每个查询提交到不同的Impala守护程序，从而实现负载平衡(`load-balance`)。  

Impala守护进程会一直的同`statestore`进行通信，以确定哪个节点是正常的能够接收新的工作。无论何时集群中的任何Impala节点创建、修改、或删除任何对象类型，还是通过Impala处理`insert,load data`语句时，它们(集群中Impala守护进程)都会从`catalogd`守护进程(在Impala1.2中引入)中接收广播消息。这种消息广播通信最大限度地减少了在Impala 1.2之前通过REFRESH或INVALIDATE METADATA语句来协调跨节点元数据。  

在Impala 2.9版本以及更高的版本，您可以控制哪些主机提供协调服务，哪些主机提供执行查询服务，以提高大型群集上高度并发工作负载的可伸缩性。  

## Impala Statestore

另一个名字为`statestore`的Impala组件服务主要用于检查集群中所有DataNodes上Impala daemons 的运行健康状况,并将状态信息的传递给每个守护进程。该服务的进程名称为`statestored`，在集群中该服务进程部署在一台主机即可。如果一个Impala守护进程由于硬件故障、网络错误、软件问题或其他原因导致下线了(`offline`),`statestore`服务会通知其他的Impala守护进程，以确保在将来执行查询能够避免向不可达节点发送请求。  

由于`statestore`服务的主要目的是帮助Impala守护进程出现错误，它对Impala集群的正常运行并不重要。如果`statestore`服务没有云行或者不可用，Impala守护进程之间会像以往正常的运行、分发任务。如果其他Impala守护进程在`statestore`脱机时失败，则集群变得不那么健壮。当`statestore`重新联机时，它会重新建立与Impala守护程序的通信并恢复其监视功能。

## Impala Catalog Service

`catalog service`是Impala组件中的另一个服务，它主要向集群中的所有DataNodes节点传递(通过`statestore`守护进程)来自Impala SQL语句执行时元数据的变化。该服务的进程名称为`catalogd`,在集群中该服务进程部署在一台主机即可.因为请求是通过`statestore`守护程序传递的，因此在同一主机上运行`statestored`和`catalogd`服务是有意义的。  

当通过Impala发出的SQL语句执行引起元数据更改时，`catalog`服务不需要执行`REFRESH` 和 `INVALIDATE METADATA`语句来向Impala守护进程同步元数据。当通过Hive来创建表、加载数据等，需要在Impala节点执行`REFRESH` 和 `INVALIDATE METADATA`，然后再在其中执行查询。  

> 通过Impala来执行`create`、`insert` 或者其他操作改变了表或数据，`REFRESH` 和 `INVALIDATE METADATA`语句不是必须执行的。如果是通过Hive操作或者直接在HDFS操作数据，那么`REFRESH` 和 `INVALIDATE METADATA`语句是需要执行的，但是在那种情况下只需要在其中的一个Impala守护进程执行就行而不是所有的节点。

默认情况下，在Impala启动的时候采用异步方式加载元数据并缓存，因此Impala可以立即开始接受请求，要启用原始行为，Impala会在接受所有请求之前等待所有元数据加载。

## Impala SQL语法

Impala的语法支持的语法是HiveQL语句、数据类型和内建方法的子集。
对于用户而言，如果对传统的RDMS关系型数据库(`traditional database`)或数据仓库(`data warehousing`)背景的,有类似的SQL操作语法:  

* 共同特性:

> 1. 都可以使用`SELECT`语句，并可以同`WHERE`、`GROUP BY`、`ORDER BY`和`WITH`语句使用，同时也可使用`Join`操作和一些用于快速处理字符串、数字和日期的内建方法(`built-in functions`).其次还包含一些聚合函数(`aggregate functions`)、子查询(`subqueries`)、比较操作(`comparison operators`)，此外还支持使用`IN`和`BETWEEN`。
> 2. 对于数据仓库而言，对分区表是比较熟悉的，同样地Impala也支持分区表`partitioned tables`。且在使用`WHERE`条件查询时将跳过所有不匹配数据，极大程度减少了查询时的I/O操作。
> 3. 在Impala 1.2版本或者更高版本的，能够支持用户自定义`UDFs`来执行查询逻辑.

* Impala特有特性:

> 1. Impala语句主要注重查询，因此对`DML`操作有些限制.Impala SQL不支持`UPDATE`和`DELETE`语句.用户可以通过`DROP TABLE` 或者`ALTER TABLE ... DROP PARTITION`语句来清除过时的数据，或者使用`INSERT OVERWRITE`语句来替换过时的数据。
> 2. 在Impala中所有数据的创建通过`INSERT`语句完成的，这些语句通常通过从其他表中查询来批量插入数据。`INSERT`具有有两种形式：`INSERT INTO` 用于向已存在的数据中追加数据。`INSERT OVERWRITE` 操作会完全的替代表或者分区的内容，对数据进行覆盖插入。语句`INSERT ... VALUES`使用单条语句来对小量数据进行插入操作，但是对于从另一个表中进行大量数据的复制和转换插入操作，那么使用另一种的单语句`INSERT ... SELECT`操作效率更高效。
> 3. 你可以在其他的环境中构建Impala表定义个表数据，然后使用Impala来实时查询，这些数据文件和表元数据可以同Hadoop生态系统中其他组件共享。事实上，Impala能够访问由Hive操作创建的表或者由Hive操作插入的数据，同样地Hive也能够访问Impala创建的表和数据，他们之间可以共享元数据信息库。许多其他的Hadoop组件可以采用如Parquet、Avro等存储格式写入文件，那么也可以通过Impala进行查询。
> 4. Hadoop和Impala对大量数据集的操作主要聚焦在数据仓库上，因此Impala有些与传统数据库不一致的地方，如可以创建外部表`external tables`.

## Impala Metadata and the Metastore

关于表的定义的相关信息，Impala使用一种叫做`metastore`的中心数据库来维持。对于拥有大量数据或很多分区的表而言，检索表的元数据需要花费很多时间，因此Impala的每个节点缓存了表的元数据以便将来查询相同表时能够重用元数据。在Impala 1.2版本以及更高的版本通过Impala发布的所有的DDL和DML语句，Impala节点上的元数据是自动更新的，这种更新方式通过`catalogd`守护进程来协调的。如果表中的数据或表的定义被更新了，在对这个表发布查询之前，所有的其他Impala守护进程必须要接收最新的元数据以替代老的缓存元数据。  

对于通过Hive发布的DDL和DML或者手动更改了HDFS中的文件，那么还需要使用`REFRESH`语句(当向已存在表中添加新的数据文件时)或`INVALIDATE METADATA`语句(对于全新的表，或删除表，对HDFS执行负载均衡操作、或删除数据文件等)来更新元数据.通过发布`INVALIDATE METADATA`方式，它自身会检索由Metastore跟踪的所有表的元数据。如果你知道哪些表被Impala以外的操作更新，你可以为每个受影响的表发出`REFRESH table_name`以仅检索这些表的最新元数据。

## Guidelines for Designing Impala Schemas

* 相对基于文本格式，首选二进制格式(Prefer binary file formats over text-based formats)

  为了能够节约内存空间及提升内存的使用率和查询性能，对于任何大表或密集查询的表使用二进制文件格式。你可能已经接触到了HaoopETL中的一部分，对于数据仓库风格的查询分析，Parquet文件格式是最高效的，此外Avro是Impala支持的另一种二进制文件格式.  

  尽管Impala能够使用RCFile和SequenceFile的格式创建表和查询表，由于这些格式是基于文本格式的，使用这些存储格式的表相对比较'笨重'(占用空间大且查询效率低下)。此外这些格式是面向行存储的，对于数据仓库的查询这些表也没有被优化。使用这些存储格式的表，Impala不支持`INSERT`操作.  

  如何选择合适的存储格式是Impala执行高效查询的关键,下面给出一些指导建议:
  + 对于表比较大、执行性能要求严格且高效可扩展的，使用Parquet文件格式。
  + 为了在ETL处理过程中传送中间数据给其他Hadoop组件，这样的数据存储格式Avro是比较合理的选择。
  + 为了方便的导入原始数据，使用文本数据表替代RCFile和SequenceFile格式，在后续的ETL处理过程中再转换未Parquet格式.

* 生产实践中使用Snappy压缩(Use Snappy compression where practical)
  
  Snappy压缩在进行解压缩时消耗比较低的CPU，且能够节省大量的存储空间。如果您可以选择压缩编解码器（例如Parquet和Avro文件格式），请使用Snappy压缩，除非您找到使用其他编解码器的令人信服的理由。

* 相对于String，优选Numeric类型(Prefer numeric types over strings)
  
  如果有些数值类型可以被看做是string类型或者数字类型(例如年、月、日等)，把它们定义为最小的适用整数类型。例如年可以设置为SMALLINT,月份和日设置为TINYINT。尽管你可能看不到分区表或文本文件在磁盘上的布局方式有任何区别，但是使用数字类型在使用二进制格式（如Parquet）存储时会节省空间，并在执行查询时节省内存，尤其是资源密集型查询（如连接）。

* 分区但是不要过度(Partition, but do not over-partition)
  
  分区是Impala调优过程中重要的一部分，如果你是从传统数据库系统转过来的或者刚进入大数据领域，在你原有的分区模式中可能没有足够量的大数据来展现Impala并行查询的优势。比如，如果你每天产生的数据量大于几十MB，采用YEAR、MONTH、DAY的方式进行分区太过细化。针对一天的数据集群中的大多数据节点在查询过程中可能处于空闲状态或者每个节点计算时间比较少。这个时候可以考虑减少分区的列key，为了让每个分区目录包含大约有几个GB的数据。再如，假设每个数据文件是Parquet表且恰巧为1个HDFS块(块的最大值为1GB)。如果你有10个节点的集群，你需要10个这样的数据文件给每个节点来执行查询工作。但是每台机器上的每个核心都可以并行处理单独的数据块。对于拥有10个节点且机器核心数据为16的集群，每次查询能够并行的处理高达160GB数据。 如果每个分区只有少量数据文件，则不仅大多数群集节点在查询期间处于空闲状态，那么这些机器上的大多数核心也处于空闲状态。你可减少Parquet块的大小到128M或者是64MB，以此来增加每个分区的文件数量且提升了并行度。但也要考虑降低分区的程度，以便分析查询有足够的数据可以使用。

* 在加载数据后总是计算stats(Always compute stats after loading data.)
  
  在整个表和表中每一列，Impala充分的的使用这些数据的统计信息为了能够为密集型操作(例如join操作)制定合适的执行计划。由于这个统计信息仅在加载数据后可用，因此对一个表或者分区在加载数据或替换数据后需要运行`COMPUTE STATS`语句来进行数据信息统计。拥有精准的统计信息在成功执行操作和失败(由于内存溢出或超时引起的失败)之间有很大差异.当你遇到了性能或容量问题，请使用`SHOW STATS`语句来检测是否所有的表在查询时的统计信息是否达到最新。

## HiveQL Features not Available in Impala

有些的HiveQL特征在当前的Impala版本中不受支持：

- `TRANSFORM`、自定义文件格式、自定义SerDes.
- `DATE`数据类型
- XML和JSON功能
- 一些聚合函数：covar_pop, covar_samp, corr, percentile,percentile_approx, histogram_numeric, collect_set
- 抽样
- 每个查询有多个DISTINCT子句