
Note: 设计模式  
[简单工厂设计模式](#简单工厂设计模式)  
[附录：面向对象基本概念与知识](#附录面向对象基本概念与知识)  

# 简单工厂设计模式

简单工厂设计模式是设计模式种最为简单且比较常用的设计模式。  

* 基本思想  
  创建一个工厂类从工厂中根据需求返回不同的对象。

* 案例分析  
  假设要从不同的数据源去读取数据，不同的数据源读取数据的接口不一致，客户端程序只能够获取数据源的名称，然后根据数据源的名称返回读取的数据。考虑到可以使用封装、继承和多态特性，将读取数据源封装为一个类。数据源抽象类名称为:DataSource.  

抽象类：DataSource 

```scala
abstract class DataSource{
    def  readData(name:String):String
}
```

抽象类中有一个方法名为readData从数据源读取方法。不同的数据源继承自该抽象类后实现该方法就可以使用多态满足不同数据源的读取。这里假设当前的业务有三个数据源需要读取分别是：

- FileDataSource(文件数据源)指定的文件名并从文件名中读取数据。
- MySqlDataSource(数据库数据源读取)从指定的数据表中读取数据。
- HiveDataSource(Hive数据源)从Hive的数据表中读取数据。

以下分别来实现这三个类:  

具体类：FileDataSource

```scala
class FileDataSource extends DataSource{
    override def readData(name:String):String={
        // todo something
    }
}
```

具体类：MySqlDataSource

```scala
class MySqlDataSource extends DataSource{
    override def readData(name:String):String={
        // todo something
    }
}
```

具体类：HiveDataSource

```scala
class HiveDataSource extends DataSource{
    override def readData(name:String):String={
        // todo something
    }
}
```

这三个类实现完毕，现在在客户端使用这三个类，你可能会这样做.  

```scala
// main code
val sourceType="hive"
val dataSource:DataSource = sourceType match{
    case "hive" => new HiveDataSource
    case "mysql" => new MySqlDataSource
    case "file" => new FileDataSource
    case _=> println("Unsupport data source to read!")
}

val content= dataSource.readData("file")
println(content)

```

在客户端这样写确实是可以使用，但是如果你要是新增一个数据源比如HBase数据源，那么这时候你需要修改客户端的代码，假设此时你的客户端代码已经提交了部署，那么你就要重新的编译部署。此外如果不小心对代码进行了其他操作可能会导致在使用其他数据源时不能够正常执行。也就是说这种在客户端修改代码会造成了代码的可维护性及可扩展性降低。另外我们可以考虑，是否有一种方法可以直接根据数据源名称而不修改客户端代码？或者说直接返回一个需要的数据源对象。可以考虑使用简单工厂模式。  
简单工厂设计模式就如同一个工厂，这个工厂只用来造"对象"，根据需求直接返回所需的对象即可。  

简单工厂类名：

```scala
object DataSourceFactory{
    def getDataSource(sourceType:String):DataSource={
        sourceType match{
            case "hive" => new HiveDataSource
            case "mysql" => new MySqlDataSource
            case "file" => new FileDataSource
            case _=> println("Unsupport data source to read!")
       }
    }
}
```

在客户端的代码可以修改为：  

```scala

val sourceType="hive"
val dataSource:DataSource=DataSourceFactory.getDataSource(sourceType)
val content= dataSource.readData("file")
println(content)

```

此时如果有的数据源添加进来只需要对将该数据源继承自DataSource类和修改DataSourceFactory方法即可，而不需要修改客户端的代码，也更方便的对新增的数据源读取功能进行测试。

* 应用场景  
  简单工厂模式主要是用来构造输出类对象的。其主要的思想是在利用封装、继承和多态。封装即为将公用操作的部分封装为一个类,如DataSource.继承则表现为具体类的实现或者自己特有的功能.多态表现为根据实例化对象的不同，父类将自动的调用子类实现的方法。  
  简单工厂模式中的工厂方法(即getDataSource)一定是静态的吗？首先从方法的实现中可以看到工厂方法主要是用于返回一个类的对象，而每个类对象都采用了`new`关键字进行创建对象，因此每次将产生一个新的实例对象出来。因此工厂方法可以不是静态，但是不建议这么做。因为该工厂方法是公用操作，可能会频繁的使用。如果不是静态的方法，在每次使用时都需要先实例化工厂类，在用实例化的对象去调用，在类的实例化时时比较耗时的操作，应当尽可能的避免。如果是静态方法在类被加载到虚拟机中的时候就已经在静态域做了存储，可以直接进行调用。(//TODO  这句话说法可能不对，但是想要表达的是静态方法可以直接调用而不需要进行实例化，因为静态方法属于类而非类对象。)  

* 模式对比  
  暂时没有可比较的设计模式。

# 附录：面向对象基本概念与知识