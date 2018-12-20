
# 关于使用 dfs.client.read.shortcircuit 配置引起的相关异常信息

加载`libhadoop`文件失败

> java.lang.RuntimeException: Although a UNIX domain socket path is configured as /var/run/hadoop-hdfs/dn._PORT, we cannot start a localDataXceiverServer because libhadoop cannot be loaded.

异常原因：在启动DataNode时需要使用hadoop的native库，首先通过以下命令检测本地的native是否通过:`hadoop checknative`.

```bash
hadoop checknative

# 得到如下结果
# hadoop:  true /home/hadoop/apps/hadoop-2.8.4/lib/native/libhadoop.so.1.0.0
# zlib:    false
# snappy:  false
# lz4:     true revision:99
# bzip2:   false
# openssl: true /usr/lib64/libcrypto.so


file /home/hadoop/apps/hadoop-2.8.4/lib/native/libhadoop.so.1.0.0
# /home/hadoop/apps/hadoop-2.8.4/lib/native/libhadoop.so.1.0.0: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, not stripped

```

说明`zlib`、`snappy`和`bzip2`不满足条件，另外也可以查看`${HADOOP_HOME}lib/native/libhadoop.so.1.0.0`文件是否是64位的。因此如果直接启动DataNode必然会报错的。另外在网上下载的别人已经编译好的native文件替代发现还是无法启动DataNode。于是自己就对Hadoop的源码做了编译。(这只是一种解决方式，可能还有另外的解决办法。).关于如何Hadoop的源码参考另一篇文章[Centos 6.10 编译Hadoop-2.8.4源码](handnote/hadoop/hadoop-compile-linux-x64.md '64位Centos编译hadoop-2.8.4源码').将的native文件替换原有的`${HADOOP_HOME}lib/native`目录下的文件。替换完成后重新启动DataNode节点.  

理论上讲这时候DataNode应该能够启动成功(如果你启动成功就恭喜你了!)，但是对于我的集群环境而言启动仍旧失败，这是令人比较费解的。因此在`/etc/profile`中手动的指定了native的目录路径(需要使用`source /etc/profile`),配置如下:

```bash
export HADOOP_HOME=/home/hadoop/apps/hadoop
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib:$HADOOP_COMMON_LIB_NATIVE_DIR"
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
```

但是重新启动DataNode依旧失败，于是乎重新检查了`hadoop-env.sh`是否存在配置项做了干扰，最后在该文件的末尾追加了如下的配置:

```bash
export HADOOP_HOME=/home/hadoop/apps/hadoop
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib:$HADOOP_COMMON_LIB_NATIVE_DIR"
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
```

再次运行DataNode还是启动失败，但是错误信息已经发生了改变，错误信息如下:

> java.io.IOException: failed to stat a path component: '/file:' in 'file:///home/hadoop/apps/tmp/dfs/hadoop-hdfs/dn.50010'. error code 2 (No such file or directory). Ensure that the path is configured correctly.

出现该问题的原因是在`hdfs-site.xml`文件中的配置项`dfs.domain.socket.path`路径配置错误导致，在配置该路径时不需要指定`file:///`,直接使用本地的目录就行，形如:

```xml
<property>
    <name>dfs.domain.socket.path</name>
    <value>${hadoop.tmp.dir}/dfs/hadoop-hdfs/dn._PORT</value>
</property>
```

随后又重新启动了DataNode，发现依然是失败的，失败的错误信息如下:

> java.io.IOException: The path component: '/home/hadoop/apps/tmp' in '/home/hadoop/apps/tmp/dfs/hadoop-hdfs/dn.50010' has permissions 0775 uid 500 and gid 500. It is not protected because it is group-writable and not owned by root. This might help: 'chmod g-w /home/hadoop/apps/tmp' or 'chown root /home/hadoop/apps/tmp'

根据提示信息可以看到`/home/hadoop/apps/tmp/dfs/hadoop-hdfs/dn.50010`这个文件的权限不能是755，要求Group内的用户不具有写权限.实际上这个目录实现创建好了，且tmp目录下的权限恰巧是755，因此需要修改文件的权限。命令如下:

```shell
chmod -R g-w ${hadoop.tmp.dir}/dfs/hadoop-hdfs
```

紧接着又重新启动了DataNode，发现仍旧失败，错误信息如下:
> java.net.BindException: bind(2) error: Address already in use when trying to bind to '/home/hadoop/apps/tmp/dfs/hadoop-hdfs/dn.50010'

出现该错误的原因是我之前手动的传创建了`dn.50010`这个目录，将这个目录删除即可，启动时会自动创建.再次启动发现成功了。最后的`hdfs-site.xml`文件的配置如下:

```xml
<configuration>

<property>
    <name>dfs.namenode.secondary.http-address</name>
    <value>master01:9001</value>
</property>

<property>
    <name>hadoop.tmp.dir</name>
    <value>/home/hadoop/apps/tmp</value>
</property>

<property>
    <name>dfs.namenode.name.dir</name>
    <value>file://${hadoop.tmp.dir}/dfs/name</value>
</property>

<property>
    <name>dfs.datanode.data.dir</name>
    <value>file://${hadoop.tmp.dir}/dfs/data</value>
</property>

<property>
    <name>dfs.replication</name>
    <value>2</value>
</property>

<property>
    <name>dfs.block.size</name>
    <value>1048576</value>
</property>

<property>
    <name>dfs.webhdfs.enabled</name>
    <value>true</value>
</property>

<property>
    <name>dfs.client.read.shortcircuit</name>
    <value>true</value>
</property>

<property>
    <name>dfs.client.file-block-storage-locations.timeout.millis</name>
    <value>10000</value>
</property>

<property>
    <name>dfs.domain.socket.path</name>
    <value>${hadoop.tmp.dir}/dfs/hadoop-hdfs/dn._PORT</value>
</property>

<property>
    <name>dfs.datanode.hdfs-blocks-metadata.enabled</name>
    <value>true</value>
</property>

</configuration>
```

`hadoop-env.sh`的配置:

```bash
export HADOOP_HOME=/home/hadoop/apps/hadoop
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib:$HADOOP_COMMON_LIB_NATIVE_DIR"
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
```