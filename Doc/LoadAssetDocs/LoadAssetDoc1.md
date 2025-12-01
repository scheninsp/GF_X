
# 打包

**ResourceManager.ResourceLoader.cs / GetBinaryPath**
```
/// <summary>
/// 获取二进制资源的实际路径。
/// </summary>
/// <param name="binaryAssetName">要获取实际路径的二进制资源的名称。</param>
/// <returns>二进制资源的实际路径。</returns>
/// <remarks>此方法仅适用于二进制资源存储在磁盘（而非文件系统）中的情况。若二进制资源存储在文件系统中时，返回值将始终为空。</remarks>
public string GetBinaryPath(string binaryAssetName)
{
    ResourceInfo resourceInfo = GetResourceInfo(binaryAssetName);
    if (resourceInfo == null)
    {
        return null;
    }

    if (!resourceInfo.Ready)
    {
        return null;
    }

    if (!resourceInfo.IsLoadFromBinary)
    {
        return null;
    }

    if (resourceInfo.UseFileSystem)
    {
        return null;
    }

    return Utility.Path.GetRegularPath(Path.Combine(resourceInfo.StorageInReadOnly ? m_ResourceManager.m_ReadOnlyPath : m_ResourceManager.m_ReadWritePath, resourceInfo.ResourceName.FullName));
}
```

ResourceInfo 是 ResourceManager 内部的一个 private sealed class，定义在Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceInfo.cs。


IsLoadFromBinary 是 ResourceInfo 的只读属性，其值由资源的 LoadType 决定。如果 LoadType
为 LoadFromBinary、LoadFromBinaryAndQuickDecrypt 或 LoadFromBinaryAndDecrypt，则
IsLoadFromBinary 为 true。每个资源的 LoadType 在资源版本列表文件（如
GameFrameworkVersion.dat）中定义，这些文件由资源构建工具在创建 AssetBundle
时生成，该工具会检查每个资产并确定其 LoadType。非标准 Unity
资产通常被标记为二进制文件。

**ResourceManager.ResourceInfo.cs \ ResourceInfo**
```
/// <summary>
/// 初始化资源信息的新实例。
/// </summary>
/// <param name="resourceName">资源名称。</param>
/// <param name="fileSystemName">文件系统名称。</param>
/// <param name="loadType">资源加载方式。</param>
/// <param name="length">资源大小。</param>
/// <param name="hashCode">资源哈希值。</param>
/// <param name="compressedLength">压缩后资源大小。</param>
/// <param name="storageInReadOnly">资源是否在只读区。</param>
/// <param name="ready">资源是否准备完毕。</param>
public ResourceInfo(ResourceName resourceName, string fileSystemName, LoadType loadType, int length, int hashCode, int compressedLength, bool storageInReadOnly, bool ready)
{
    m_ResourceName = resourceName;
    m_FileSystemName = fileSystemName;
    m_LoadType = loadType;
    m_Length = length;
    m_HashCode = hashCode;
    m_CompressedLength = compressedLength;
    m_StorageInReadOnly = storageInReadOnly;
    m_Ready = ready;
}
```

FileSystemName 是 Game Framework 中自定义文件系统的标识，通常对应一个 .dat 文件，如 resources.dat 或shared.dat。例如，核心UI资源打包到 UI.dat 文件时，其 ResourceInfo.FileSystemName 为"UI"；游戏关卡资源打包到 Levels.dat 时，FileSystemName 为 "Levels"。ResourceManager通过 FileSystemName定位并加载资源。

生成 dat 文件的核心代码链路如下:
1. `Assets/Plugins/UnityGameFramework/Scripts/Editor/ResourceBuilder/ResourceBuilderController.cs` -> `BuildResources()`: 启动整个资源构建流程。
2. `...` -> `BuildResources(Platform ...)`: 针对特定平台执行构建。
3. `...` -> `CreateFileSystems(...)`: 在此方法中，根据配置创建空的 .dat 文件。路径格式为：Path.Combine(outputPath, "{fileSystemName}.dat")。
4. `...` -> `ProcessOutput(...)`: 将单个资源的数据通过 IFileSystem.WriteFile()接口写入对应的 .dat 文件流中。实际的文件I/O操作由 GameFramework.FileSystem 模块封装。

  然而，在资源打包流程中，还会生成另外几种至关重要的 .dat文件，它们是资源清单文件，用于描述所有资源的信息。这些文件更有可能是您想了解的。根据代码，主要有以下三种清单文件：
   1. 可更新资源清单 (`UpdatableVersionList`): 由 ProcessUpdatableVersionList方法生成，最终保存为GameFrameworkVersion.{crc32}.dat。这是用于热更新模式的核心文件，包含了资源服务器上所有可更新的资源信息。
   2. 包内资源清单 (`PackageVersionList`): 由 ProcessPackageVersionList 方法生成，保存为GameFrameworkVersion.dat。它包含了资源包的完整信息，通常用于版本校验。
   3. 只读区资源清单 (`LocalVersionList`): 由 ProcessReadOnlyVersionList 方法生成，保存为GameFrameworkList.dat。它描述了打包在程序本体内、只读的资源。


Assets\Plugins\UnityGameFramework\Scripts\Runtime\Resource\BuiltinVersionListSerializer.UpdatableVersionListSerializeCallback.cs
UpdatableVersionListSerializeCallback_V2

  `UpdatableVersionList` (V2) 文件格式

  1. 加密密钥
   - 随机加密Key (byte[], 4字节)
     - 文件开头的4个字节是一个随机生成的密钥。后续所有标记为 "加密字符串"的字段都使用此密钥进行简单的异或加密。

  2. 文件头信息
   - 适用游戏版本号 (加密字符串)
     - 例如 "1.0.0"，用于标识此资源列表对应的游戏版本。
   - 内部资源版本号 (7-bit Encoded Int32)
     - 整型的资源版本号，用于增量更新判断。7-bit Encoded
       是一种可变长度的整数编码，用于节省空间。

  3. 资产列表 (Assets)
   - 资产总数 (7-bit Encoded Int32)
   - [循环 `资产总数` 次] 每个资产的信息：
       - 资产名称 (加密字符串)
         - 资产的完整路径名，例如 "Assets/Prefabs/MyUI.prefab"。
       - 依赖资产数量 (7-bit Encoded Int32)
       - [循环 `依赖资产数量` 次]
           - 依赖资产索引 (7-bit Encoded Int32)
             - 该依赖资产在 "资产列表" 中的索引。

  4. 资源列表 (Resources)
   - 资源总数 (7-bit Encoded Int32)
   - [循环 `资源总数` 次] 每个资源（AssetBundle）的信息：
       - 资源名称 (加密字符串)
         - 资源名，例如 "myui_prefab"。
       - 变体名称 (加密字符串)
         - 资源的变体名(variant)，例如 "sd" 或 "hd"。如果不存在则为空字符串。
       - 文件扩展名 (加密字符串)
         - 资源的文件扩展名。
       - 加载方式 (byte)
         - LoadType 枚举值，表示资源的加载方式（例如从内存加载、从文件加载等）。
       - 原始文件长度 (7-bit Encoded Int32)
       - 原始文件哈希码 (Int32, 4字节)
         - 未压缩、未加密的原始资源文件的 CRC32 哈希值。
       - 压缩后文件长度 (7-bit Encoded Int32)
       - 压缩后文件哈希码 (Int32, 4字节)
         - 压缩后文件的 CRC32 哈希值。
       - 包含资产数量 (7-bit Encoded Int32)
         - 这个资源包内包含的资产数量。
       - [循环 `包含资产数量` 次]
           - 资产索引 (7-bit Encoded Int32)
             - 包含的资产在 "资产列表" 中的索引。

  5. 文件系统列表 (File Systems)
   - 文件系统总数 (7-bit Encoded Int32)
   - [循环 `文件系统总数` 次] 每个文件系统的信息：
       - 文件系统名称 (加密字符串)
         - 所属文件系统的名称。
       - 包含资源数量 (7-bit Encoded Int32)
       - [循环 `包含资源数量` 次]
           - 资源索引 (7-bit Encoded Int32)
             - 属于此文件系统的资源在 "资源列表" 中的索引。

  6. 资源组列表 (Resource Groups)
   - 资源组总数 (7-bit Encoded Int32)
   - [循环 `资源组总数` 次] 每个资源组的信息：
       - 资源组名称 (加密字符串)
         - 资源组的名称，例如 "UI"、"SceneA" 等。
       - 包含资源数量 (7-bit Encoded Int32)
       - [循环 `包含资源数量` 次]
           - 资源索引 (7-bit Encoded Int32)
             - 属于此资源组的资源在 "资源列表" 中的索引。


生成 .dat 文件的逻辑是一个通用的资源处理流程，它会遍历所有待处理的 AB 包，并逐个生成对应的 .dat 文件。
关键的函数是 private bool BuildResources(Platform platform, ...)。在这个函数内部，有一个循环会遍历所有被识别为 AssetBundle 的资源。
```
private bool BuildResources(Platform platform, AssetBundleBuild[] assetBundleBuildDatas, BuildAssetBundleOptions buildAssetBundleOptions, ResourceData[] assetBundleResourceDatas, ResourceData[] binaryResourceDatas)
{
        for (int i = 0; i < assetBundleResourceDatas.Length; i++)
        {
            ProcessAssetBundle
        }
}
```

```
private bool ProcessAssetBundle(Platform platform, string workingPath, string outputPackagePath, string outputFullPath, string outputPackedPath, bool additionalCompressionSelected, string name, string variant, string fileSystem)
{
   return ProcessOutput(platform, outputPackagePath, outputFullPath, outputPackedPath, additionalCompressionSelected, name, variant, fileSystem, resourceData, bytes, length, hashCode, compressedLength, compressedHashCode);
}


```
ProcessAssetBundle 直接将 ab 包使用
byte[] bytes = File.ReadAllBytes(workingName); 读入
然后在 processOutput 中，再用 File.WriteAllBytes 输出到自己的文件系统


```
ResourceBuilderController:ProcessAssetBundle 992
ResourceBuilderController:BuildResources 914
ResourceBuilderController:BuildResources 689
AppBuildEidtor:BuildResources 1049
AppBuildEidtor:Update 154
HostView:SendUpdate -1
EditorApplication:Internal_CallUpdateFunctions -1
```

ProcessAssetBundle 参数
platform Windows64
workingPath "D:/UnityProjects/GF_X/GF_X/AB/Working/Windows64/"
outputFullPath "D:/UnityProjects/GF_X/GF_X/AB/Full/1_0_0_1/Windows64/"
outputPackedPath "D:/UnityProjects/GF_X/GF_X/AB/Packed/1_0_0_1/Windows64/"
additionalCompressionSelected true
name "Config"
variant null
fileSystem null

name "Core","DataTable","Entity","HotfixDlls",
"Language","Scene","ScriptableAssets","SharedAssets","UI"


ProcessAssetBundle 中的 m_ResourceDatas 来源于 m_ResouceCollection
```
private bool PrepareBuildData(out AssetBundleBuild[] assetBundleBuildDatas, out ResourceData[] assetBundleResourceDatas, out ResourceData[] binaryResourceDatas) {
    Resource[] resources = m_ResourceCollection.GetResources();
    foreach (Resource resource in resources)
    {
        m_ResourceDatas.Add(resource.FullName, new ResourceData(resource.Name, resource.Variant, resource.FileSystem, resource.LoadType, resource.Packed, resource.GetResourceGroups()));
    }
}

```

m_ResouceCollection 来源 ResourceCollection.xml
Assets\Plugins\UnityGameFramework\Configs\ResourceCollection.xml
ResourceCollection.xml  来自 Resource Editor ，菜单栏工具

## ResouceCollection.xml 中指定的大区分
Config
游戏业务配置，类似常量表
Assets\AAAGame\Config\GameConfig.txt
GameConfig.bytes

Core
GFExtension.prefab
  总结来说，GFExtension.prefab是一个在游戏启动时就应该被实例化的核心对象。它集成了数管理（DataModel）、全局变量（VariablePool）和常驻的核心UI（如加载界面和摇杆）等功能，为游戏提供了一个便利、统一的管理框架。

DataTable
Assets/AAAGame/DataTable 中的内容

Entity
实体 prefab
例如 Bullet.prefab, FireFx.prefab, MyPlayer.prefab ...

HotfixDlls
HybridCLR 热更信息
包含 Assets\AAAGame\HotfixDlls\Hotfix.bytes 和 HotfixFileList.txt

Language
语言。

Scene
所有场景。Game.unity, Launch.unity

ScriptableAssets
Assets\AAAGame\ScriptableAssets\Core\AppConfigs.asset
游戏流程控制，数据表包含信息，Config, Launguage
类似于一个总索引

SharedAssets
字体，贴图，Shader

UI
UI prefabs

上面的都会被分配到不同的 dat 文件



MyPlayer.prefab 被明确分配到了 Entity 资源组。
PlayerCtrl.controller 和 Humanoid@IdleHold2Guns.FBX 作为 MyPlayer.prefab的依赖项，并且它们本身没有在 ResourceCollection.xml 中被分配到任何其他的资源组。
因此，为了保证 MyPlayer.prefab 在加载后能找到它的所有依赖，打包工具会将 PlayerCtrl.controller 和 Humanoid@IdleHold2Guns.FBX 都打包到 MyPlayer.prefab 所在的 AB 包中，也就是 Entity 组对应的那个包。


GF_X\AB\Full\1_0_0_1\Windows64\version.json 的内容如下：
```
    1 {
    2     "InternalResourceVersion": 1,
    3     "VersionListLength": 3661,
    4     "VersionListHashCode": -150839323,
    5     "VersionListCompressedLength": 1477,
    6     "VersionListCompressedHashCode": -1320346421,
    7     "ApplicableGameVersion": "1.0.0|1.0.1|1.0.2",
    8     "UpdatePrefixUri": "http://127.0.0.1:8080/1_0_0_1/Windows64",
    9     "LastAppVersion": "1.0.0",
   10     "ForceUpdateApp": false,
   11     "AppUpdateUrl": "https://play.google.com/store/apps/details?id=",
   12     "AppUpdateDesc": "1. bug fix.\n2. add xxx"
   13 }
```

# 打 UnityAB 包

资产依赖分析
```
ResourceAnalyzerController:AnalyzeAsset 141
ResourceAnalyzerController:AnalyzeAsset 194
ResourceAnalyzerController:Analyze 115
ResourceBuilderController:BuildResources 656
AppBuildEidtor:BuildResources 1049
AppBuildEidtor:Update 154
HostView:SendUpdate -1
EditorApplication:Internal_CallUpdateFunctions -1
```

资产依赖分析主入口
ResourceAnalyzerController.cs
```
public void Analyze(){

    Asset[] assets = m_ResourceCollection.GetAssets();

}

```


获取资产依赖 AssetDatabase.GetDependencies
```
//hostAsset : ResourceCollection.xml 中指定的大区分
//dependencyData : Editor\ResourceAnalyzer\DependencyData.cs
//

private void AnalyzeAsset(string assetName, Asset hostAsset, DependencyData dependencyData, HashSet<string> scriptAssetNames)
{
        string[] dependencyAssetNames = AssetDatabase.GetDependencies(assetName, false);
}
```

## DependencyData

### Resource

一个 resource 对应 ResourceCollection.xml 中定义的一个大分区中的一个“资源”
可能是单一的一个 Asset，也可能是一组 Asset

Resouce: ResourceCollection\Resource.cs
```
m_Assets = new List<Asset>();
m_ResourceGroups = new List<string>();

Name = name;
Variant = variant;
AssetType = AssetType.Unknown;
FileSystem = fileSystem;
LoadType = loadType;
Packed = packed;
```
对应一个 ab 包？ name, variant 是 ab 包名 Name.Variant?
FileSystem，LoadType，Packed 是加载 ab 包时的策略


### LoadType
  LoadFromFile 和 LoadFromBinary 都是资源加载方式的选项，它们的主要区别在于如何处理 AssetBundle 文件。

   1. `LoadFromFile` (从文件加载)
       * 注释: "使用文件方式加载。"
       * 工作方式: 这是通过 AssetBundle.LoadFromFile API 来实现的。它直接从磁盘上的文件路径加载资源包。
       * 优点: 内存效率非常高。它不会将整个 AssetBundle
         文件完整地读入内存，而是根据需要从磁盘流式加载数据。这是大多数情况下的首选方式。

   2. `LoadFromBinary` (从二进制流加载)
       * 注释: "使用二进制方式加载。"
       * 工作方式: 这是通过 AssetBundle.LoadFromMemory API 实现的。它需要先将整个 AssetBundle
         文件的内容读入一个内存中的字节数组 (byte[])，然后再从这个内存数组中加载资源包。
       * 应用场景: 这种方式主要用于那些无法直接通过文件路径加载的场景，最典型的就是
         资源加密。你需要先将加密的文件读入内存，解密成原始的 AssetBundle 字节数据，然后再调用
         AssetBundle.LoadFromMemory 来加载。
       * 缺点: 会占用更多内存，因为内存中除了有 Unity
         加载资源所需的内存外，还有一个完整的资源包字节数组副本。

  ResourceManager
  内部维护了两套完全不同的加载逻辑：一套用于加载"资产"（Asset），另一套用于加载"二进制流"（Binary）。

  1. LoadFromMemory (及其变种)

   * 最终目的： 加载 Unity 资产 (Asset)。
   * 调用接口： ResourceManager.LoadAsset() 或 ResourceManager.LoadScene()。
   * 内部流程：
       1. 框架将资源文件（一个 AssetBundle）的字节读入内存。
       2. 如果 LoadType 是 LoadFromMemoryAndDecrypt 等加密类型，则执行解密。
       3. 框架调用 AssetBundle.LoadFromMemory() 将字节数组转换成一个 AssetBundle 对象。
       4. 从这个 AssetBundle 对象中加载出你指定的具体资产（比如 "Assets/UI/MainMenu.prefab"）。
       5. 返回给你的是一个 GameObject、Texture2D 或 TextAsset 等 Unity 对象。
   * 代码证据： 在 ResourceManager.ResourceLoader.cs 的 LoadAsset 方法中，代码会检查
     resourceInfo.IsLoadFromBinary。如果为 true，则直接报错，这证明了 LoadFromBinary 不能用于加载资产。

  2. LoadFromBinary (及其变种)

   * 最终目的： 加载文件的原始字节 (byte[])。
   * 调用接口： ResourceManager.LoadBinary()。
   * 内部流程：
       1. 框架将文件（可以是任何类型的文件，不一定是 AssetBundle）的字节读入内存。
       2. 如果 LoadType 是 LoadFromBinaryAndDecrypt 等加密类型，则执行解密。
       3. 加载流程结束。
       4. 返回给你的是一个 `byte[]` 数组。你可以用这个数组去反序列化 JSON、XML，或者解析自定义的二进制数据。
   * 代码证据： LoadBinary 方法会检查
     !resourceInfo.IsLoadFromBinary，如果不是二进制加载类型，就会报错。这证明了 LoadAsset 和 LoadBinary
     的路径是完全分开的。

一个 Asset 对应一个具有 guid 的 Unity 资产
一个 Asset 只能存在于一个 Resource 内
### Asset
```
private Asset(string guid, Resource resource)
{
    Guid = guid;
    Resource = resource;
}
```
判断一个 ResourceCollection 中是否存在某个资产：
Asset asset = m_ResourceCollection.GetAsset(guid);



### DependencyData 生成和用途
  DependencyData 类用于在资源分析过程中，存储一个“宿主资源”（Host
  Asset）所依赖的所有其他资产和资源（AssetBundle）的信息。它包含三个核心的私有成员变量：

   * private List<Resource> m_DependencyResources;
       * 作用：存储所有被依赖的 资源（`Resource`） 列表。在 GameFramework 的资源系统中，一个 Resource通常代表一个 AssetBundle 文件。此列表是去重后的，即一个 AssetBundle无论被多少个资产依赖，在这里只会出现一次。
       * 目的：用于最终统计宿主资源依赖了多少个不同的 AssetBundle。

   * private List<Asset> m_DependencyAssets;
       * 作用：存储所有被依赖的 资产（`Asset`） 列表。一个 Asset 是 AssetBundle 中的具体内容，例如一个Prefab、一张 Texture、一个 AudioClip 等。
       * 目的：提供一份详细的、被宿主资源直接或间接依赖的、且已正确配置在某个 Resource (AssetBundle)中的所有资产清单。

   * private List<string> m_ScatteredDependencyAssetNames;
       * 作用：存储所有被依赖的 “散乱”资产的名称（路径）。
       * 目的：这是非常关键的一个列表，它用于识别那些被依赖了，但是没有被配置到任何 `Resource` (AssetBundle)中的资产。这些通常是资源配置中的遗漏项或错误。例如，一个 Prefab依赖了一张贴图，但这张贴图没有被标记到任何 AssetBundle中，那么这张贴图的路径就会被记录到这个列表里。

总结：
在整个 AnalyzeAsset 的递归分析过程中，dependencyData 对象就像一个不断被填充的篮子：
   * 当遇到一个配置正确的依赖资产时，就把这个资产本身丢进 m_DependencyAssets 篮子，并把它所属的 AssetBundle 丢进 m_DependencyResources 篮子（如果篮子里还没有的话）。
   * 当遇到一个未配置的依赖资产（即“散乱”资产）时，就把这个资产的名字（路径）写在一张纸条上，丢进
     m_ScatteredDependencyAssetNames 篮子。

例：
MyPlayer.prefab 在 AnalyzeAsset 过程中，分析到 fbx 时的情况
m_DependencyAssets 为空
m_DependencyResources 为空
m_ScatteredDependencyAssetNames	Count = 4
"Assets/AAAGame/Materials/Player.mat"
"Packages/com.unity.render-pipelines.universal/Shaders/SimpleLit.shader"
"Assets/AAAGame/Animation/PlayerCtrl.controller"
"Assets/AAAGame/Animation/Humanoid@death.fbx"


# BuildResources 生成 ab 包

```
private bool BuildResources(Platform platform, AssetBundleBuild[] assetBundleBuildDatas, BuildAssetBundleOptions buildAssetBundleOptions, ResourceData[] assetBundleResourceDatas, ResourceData[] binaryResourceDatas)
```
注意 assetBundleBuildDatas 这个数组输入时为空，函数内处理，输出就是要打的 ab 包的列表

准备 `AssetBundleBuild` 列表
      AssetBundleBuild 是 Unity 的一个结构体，它只有两个关键成员：
       * string assetBundleName：要生成的 AssetBundle 的名字。
       * string[] assetNames：一个字符串数组，包含了所有要打进这个 AssetBundle 的资产路径。


在 BuildResources 方法中，您会看到类似下面这样的逻辑（为了便于理解，我将代码逻辑简化并展示）：
这里 assetBundleBuilds 就是简化后的 assetBundleBuildDatas
```
    1     // 这是一个简化版的逻辑，实际代码会更复杂
    2     List<AssetBundleBuild> assetBundleBuilds = new List<AssetBundleBuild>();
    3
    4     // 遍历所有从 ResourceCollection 中获取的、被标记为需要打包(Packed)的 Resource
    5     foreach (Resource resource in allPackedResources)
    6     {
    7         AssetBundleBuild assetBundleBuild = new AssetBundleBuild();
    8
    9         // 1. 设置 AssetBundle 的名字，来自于 Resource.FullName
   10         assetBundleBuild.assetBundleName = resource.FullName;
   11
   12         // 2. 获取这个 Resource 包含的所有 Asset
   13         Asset[] assets = resource.GetAssets();
   14         string[] assetNames = new string[assets.Length];
   15         for (int i = 0; i < assets.Length; i++)
   16         {
   17             // 3. 从 Asset 对象中获取资产的真实路径
   18             assetNames[i] = assets[i].Name;
   19         }
   20
   21         // 4. 设置这个 AssetBundle 要包含的所有资产路径
   22         assetBundleBuild.assetNames = assetNames;
   23
   24         assetBundleBuilds.Add(assetBundleBuild);
   25     }
```

3. 调用 Unity 底层接口
    当 assetBundleBuilds 列表准备好之后，就万事俱备了。最后，代码会调用 Unity 的核心打包 API
BuildPipeline.BuildAssetBundles，并将这个列表作为参数传递进去。这就是您在搜索结果中看到的那一行：

1     // L855:
2     AssetBundleManifest assetBundleManifest = BuildPipeline.BuildAssetBundles(workingPath,
    assetBundleBuildDatas, buildAssetBundleOptions, GetBuildTarget(platform));

    * workingPath: AssetBundle 的输出目录。
    * assetBundleBuildDatas: 就是我们上一步精心准备的 AssetBundleBuild 列表。
    * buildAssetBundleOptions: 打包选项（例如压缩方式、是否禁用类型树等）。
    * GetBuildTarget(platform): 目标平台（如 BuildTarget.StandaloneWindows64）。




# 加载


**ResourceManager.ResourceLoader.cs / LoadBinaryFromFileSystem**
```
/// <summary>
/// 从文件系统中加载二进制资源。
/// </summary>
/// <param name="binaryAssetName">要加载二进制资源的名称。</param>
/// <returns>存储加载二进制资源的二进制流。</returns>
public byte[] LoadBinaryFromFileSystem(string binaryAssetName)
{
    ResourceInfo resourceInfo = GetResourceInfo(binaryAssetName);
    if (resourceInfo == null)
    {
        throw new GameFrameworkException(Utility.Text.Format("Can not load binary '{0}' from file system which is not exist.", binaryAssetName));
    }

    if (!resourceInfo.Ready)
    {
        throw new GameFrameworkException(Utility.Text.Format("Can not load binary '{0}' from file system which is not ready.", binaryAssetName));
    }

    if (!resourceInfo.IsLoadFromBinary)
    {
        throw new GameFrameworkException(Utility.Text.Format("Can not load binary '{0}' from file system which is not a binary asset.", binaryAssetName));
    }

    if (!resourceInfo.UseFileSystem)
    {
        throw new GameFrameworkException(Utility.Text.Format("Can not load binary '{0}' from file system which is not use file system.", binaryAssetName));
    }

    IFileSystem fileSystem = m_ResourceManager.GetFileSystem(resourceInfo.FileSystemName, resourceInfo.StorageInReadOnly);
    byte[] bytes = fileSystem.ReadFile(resourceInfo.ResourceName.FullName);
    if (bytes == null)
    {
        return null;
    }

    if (resourceInfo.LoadType == LoadType.LoadFromBinaryAndQuickDecrypt || resourceInfo.LoadType == LoadType.LoadFromBinaryAndDecrypt)
    {
        DecryptResourceCallback decryptResourceCallback = m_ResourceManager.m_DecryptResourceCallback ?? DefaultDecryptResourceCallback;
        decryptResourceCallback(bytes, 0, bytes.Length, resourceInfo.ResourceName.Name, resourceInfo.ResourceName.Variant, resourceInfo.ResourceName.Extension, resourceInfo.StorageInReadOnly, resourceInfo.FileSystemName, (byte)resourceInfo.LoadType, resourceInfo.Length, resourceInfo.HashCode);
    }

    return bytes;
}

```



# 加载 FBX

  综合以上分析，你的 .fbx 文件被“删除”的根本原因是：

   1. 你在 App Builder 窗口中勾选了 "Enable [Rule Editor]" 选项，启用了规则模式。
   2. 这导致了构建开始时 RefreshResourceRule 逻辑被执行，它清空了你之前手动的配置。
   3. 在你的 Resource Rule Editor 的所有规则中，没有任何一条规则的 AssetDirectory 和 Search Patterns
      能够匹配并包含到你的 @Assets/AAAGame/Animation/test_strech_squash_2020_6.fbx 这个文件。
   4. 因此，在重新生成资源列表时，这个 .fbx 文件没有被任何规则捕获并添加回来。
   5. 最终，ResourceCollection.xml
      中没有这个资源的任何信息，导致它在构建过程中被彻底忽略，看起来就像是被“删除”了。
      

重新打开 Resource Rule Editor，把 fbx 放到一个单独文件夹，然后加入此文件夹，设置 Load From File
```
private void AnalyzeAsset(string assetName, Asset hostAsset, DependencyData dependencyData, HashSet<string> scriptAssetNames)
```

没有人依赖这个 fbx
这个 fbx 唯一的 dependencyAsset 是 shader
"Packages/com.unity.render-pipelines.universal/Shaders/Lit.shader"

461s 构建

# LoadAsset

```
GF.Resource.LoadAsset(
            fbxAssetPath, 
            typeof(AnimationClip), 
            new LoadAssetCallbacks(
                // 加载成功回调
                (assetName, asset, duration, userData) =>
                {
                    AnimationClip loadedClip = asset as AnimationClip;
                    if (loadedClip != null)
                    {
                        // 加载成功，asset 就是你要的 AnimationClip
                        Log.Info($"Successfully loaded AnimationClip '{loadedClip.name}' length '{loadedClip.length}' from FBX '{assetName}'.");
                    }
                    else
                    {
                        Log.Error($"Loaded asset from '{assetName}' but it was not an AnimationClip.");
                    }
                },
                // 加载失败回调
                (assetName, status, errorMessage, userData) =>
                {
                    Log.Error($"Failed to load asset '{assetName}'. Status: {status}, Error: {errorMessage}");
                }
            )
        );
```


LoadAsset 调用栈
ResourceLoader:LoadAsset 308
ResourceManager:LoadAsset 1627
ResourceComponent:LoadAsset 1050
ResourceComponent:LoadAsset 967
LoadFbxClipExample:StartLoadingClip 31


```
LoadAssetTask mainTask = LoadAssetTask.Create(assetName, assetType, priority, resourceInfo, dependencyAssetNames, loadAssetCallbacks, userData);

assetName = "Assets/AAAGame/DynamicAnimation/test_strech_squash_2020_6.fbx"
assetType = {UnityEngine.AnimationClip}  //System.Type
resourceInfo =
CompressedLength 56023
Length 56023
FileSystemName null
IsLoadFromBinary false
loadType(m_LoadType) LoadFromFile
ResourceName "DynamicAnimation.dat"
StorageInReadOnly true
UseFileSystem false   //这里为什么是

dependencyAssetNames 空

userData null
```

如果 ResourceInfo 里不是 ready 的，那么就需要去网络请求下载
```
if (!resourceInfo.Ready)
{
    m_ResourceManager.UpdateResource(resourceInfo.ResourceName);
}
```

## UseFileSystem 的说明

  在“Updatable”模式下，资源通常存储在 AssetBundle（ab 包）中。GameFramework 有两种存储资源的方式：
   1. 作为磁盘上的独立文件： 在这种情况下，m_FileSystemName 将为 null 或空，UseFileSystem 将为false。这通常适用于直接从 Unity 编辑器加载或内置到应用程序中而未打包到自定义 GameFramework文件系统中的资源。
   2. 在 GameFramework 文件系统内部： 这些是包含多个资源的自定义压缩/加密文件。如果资源是此类文件系统的一部分，则 m_FileSystemName 将包含该文件系统的名称，并且 UseFileSystem 将为 true。

  结论：
  对于 FBX 资源“Assets/AAAGame/DynamicAnimation/test_strech_squash_2020_6.fbx”，其ResourceInfo.UseFileSystem 为false，这意味着当此资源的 ResourceInfo 生成时（很可能是在 AssetBundle 或应用程序本身的构建过程中），它未被打包到GameFramework 文件系统中。相反，它被视为磁盘上的独立资源，即使它位于 AssetBundle 中。

  GameFramework 的 ResourceMode: Updatable 主要管理下载和更新哪些 AssetBundle，但这并不一定意味着这些 AssetBundle 内部 的所有资源都始终存储在 GameFramework 的自定义文件系统中。AssetBundle 本身是 Unity 的原生打包格式。如果GameFramework 没有明确将 AssetBundle 或其内容放入其自己的 IFileSystem 实现中，那么 UseFileSystem 将保持 false。

  为了证实这一点，通常会检查 GameFramework 构建设置或资源收集设置，以查看单个资源或 AssetBundle的打包配置方式。如果一个资源仅仅是“AssetBundle Packed”但未同时“File System Packed”（如果他们的特定 GameFramework配置中存在这样的区别），那么 UseFileSystem 将为 false。


对用户问题的综合回答：

用户询问了 Resource Rule Editor 配置（特别是将 `FileSystem` 字段留空）影响 `ResourceInfo.UseFileSystem` 的代码位置。

以下是端到端的跟踪：

1.  **Resource Rule Editor 配置：** 当您在 Resource Rule Editor 中将资源的 `FileSystem` 字段留空（例如“DynamicAnimation”）时，此配置会被存储，并最终在 GameFramework 构建过程（生成版本列表）中使用。当 GameFramework 运行时初始化或更新时，它会读取这些版本列表。

2.  **资源检查阶段 (`ResourceManager.OnCheckerResourceNeedUpdate`)：** 在资源检查阶段（在“Updatable”资源模式下），`ResourceManager`（特别是其内部 `ResourceChecker` 组件）会处理版本列表。当它确定某个资源需要更新或添加时，它会调用 `OnCheckerResourceNeedUpdate`。
    -   **代码位置：** `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.cs`（大约第 1709 行，`OnCheckerResourceNeedUpdate` 方法）。
    -   **解释：** 此方法接收一个 `fileSystemName` 参数。如果您在编辑器中将 `FileSystem` 字段留空，则此时的 `fileSystemName` 将是 `null` 或一个空字符串。

3.  **添加到资源更新队列 (`ResourceManager.ResourceUpdater.AddResourceUpdate`)：** `OnCheckerResourceNeedUpdate` 随后将此 `fileSystemName` 传递给 `ResourceManager.ResourceUpdater.AddResourceUpdate`。
    -   **代码位置：** `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ResourceUpdater.cs`（大约第 205 行，`AddResourceUpdate` 方法）。
    -   **解释：** 此方法为资源创建一个 `UpdateInfo` 对象，并将接收到的 `fileSystemName` 存储在其 `m_FileSystemName` 成员中。

4.  **`UpdateInfo` 存储 `fileSystemName`：** `UpdateInfo` 类（它保存有关需要更新的资源的临时信息）直接存储 `fileSystemName`。其 `UseFileSystem` 属性由此存储的值派生。
    -   **代码位置：** `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ResourceUpdater.UpdateInfo.cs`（大约第 28 行，`UpdateInfo` 构造函数及其 `UseFileSystem` 属性）。
    -   **解释：** 如果 `fileSystemName` 为空，则 `UpdateInfo.UseFileSystem` 将为 `false`。

5.  **填充 `m_ReadWriteResourceInfos` (`ResourceManager.ResourceUpdater.ApplyResource` / `OnDownloadSuccess`)：** 当资源成功应用（从资源包）或下载时，`ResourceUpdater` 会更新主 `ResourceManager` 的 `m_ReadWriteResourceInfos` 字典。它通过创建一个 `ReadWriteResourceInfo` 对象来完成此操作。
    -   **代码位置：**
        -   `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ResourceUpdater.cs`（大约第 382 行，在 `ApplyResource` 内部）。
        -   `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ResourceUpdater.cs`（大约第 664 行，在 `OnDownloadSuccess` 内部）。
    -   **解释：** 这两个方法都创建 `ReadWriteResourceInfo` 实例，将 `fileSystemName`（从 `UpdateInfo` 或 `ApplyInfo` 对象获取）传递给其构造函数。

6.  **`ReadWriteResourceInfo` 存储 `fileSystemName`：** `ReadWriteResourceInfo` 结构随后存储此 `fileSystemName`。
    -   **代码位置：** `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ReadWriteResourceInfo.cs`（大约第 12 行，`ReadWriteResourceInfo` 构造函数及其 `UseFileSystem` 属性）。
    -   **解释：** 如果 `fileSystemName` 为空，则 `ReadWriteResourceInfo.UseFileSystem` 将为 `false`。

7.  **`ResourceManager.GetResourceInfo` 检索 `ResourceInfo`：** 最后，当调用 `GF.Resource.LoadAsset`（它委托给 `ResourceManager.ResourceLoader.LoadAsset`）时，`ResourceLoader` 最终会调用 `ResourceManager.GetResourceInfo`。此方法检索资产的 `ResourceInfo` 对象。这个 `ResourceInfo` 对象本身将正确反映 `UseFileSystem` 为 `false`，因为由于您的 Resource Rule Editor 配置，其 `m_FileSystemName` 在资源处理期间最初被设置为空字符串或 `null`。
    -   **代码位置：** `Assets/Plugins/UnityGameFramework/GameFramework/Resource/ResourceManager.ResourceInfo.cs`（大约第 28 行，`ResourceInfo` 的 `UseFileSystem` 属性）。

简而言之，`ResourceInfo.UseFileSystem` 为 `false` 的决定直接源于您的 Resource Rule Editor 配置中 `FileSystem` 字段留空，它通过 GameFramework 的资源管理管道（从检查/更新到最终的 `ResourceInfo` 对象）传播。

至此，详细调查结束。




# ResourceManager.ResourceLoader.LoadAsset 到 DefaultLoadResourceAgentHelper.ReadFile

  总结流程图：
```
    1 ResourceComponent.LoadAsset (外部调用入口)
    2       ↓
    3 ResourceManager.ResourceLoader.LoadAsset (创建 LoadAssetTask)
    4       ↓
    5 m_TaskPool.AddTask (将任务加入任务池)
    6       ↓ (TaskPool 调度)
    7 LoadResourceAgent.Start(LoadAssetTask task) (代理开始处理任务)
    8       ↓ (根据 ResourceInfo 判断加载类型和是否使用文件系统)
    9 m_Helper.ReadFile(fullPath)  或  m_Helper.ReadFile(fileSystem, name) (在 DefaultLoadResourceAgentHelper
      中实现)
   10       ↓
   11 DefaultLoadResourceAgentHelper (内部调用 Unity API: AssetBundle.LoadFromFileAsync 等)
```



# LoadAssetTask

Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.LoadAssetTask.cs


## ResourceLoader 怎样关联 LoadAssetTask 和 LoadResourceAgent？

Assets\Plugins\UnityGameFramework\GameFramework\Base\TaskPool\TaskPool.cs
m_TaskPool 是一个 LoadResourceTask 类型对应的 task pool
private readonly TaskPool<LoadResourceTaskBase> m_TaskPool;
加入 m_TaskPool 之后，ResourceLoader 会在 Update 中轮询更新
```
public void Update(float elapseSeconds, float realElapseSeconds)
{
    m_TaskPool.Update(elapseSeconds, realElapseSeconds);
}
```

在 ResourceLoader.AddLoadResourceAgentHelper 方法中，是这样创建 LoadResourceAgent 并添加到m_TaskPool 的：

```
 LoadResourceAgent agent = new LoadResourceAgent(loadResourceAgentHelper, resourceHelper, this, readOnlyPath, readWritePath, decryptResourceCallback ??DefaultDecryptResourceCallback);
 m_TaskPool.AddAgent(agent);
```

## TaskPool 执行
Assets\Plugins\UnityGameFramework\GameFramework\Base\TaskPool\TaskPool.cs
```
//取出第一个 waiting task
LinkedListNode<T> current = m_WaitingTasks.First;
//存在 FreeAgent
    while (current != null && FreeAgentCount > 0)
    {
        //启动 agent
        StartTaskStatus status = agent.Start(task);
    }
```
对于 LoadAssetTask 的 task pool，agent 类型就是 LoadResourceAgent



## Agent开始执行 LoadResourceAgent.Start

Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.LoadResourceAgent.cs


先尝试从 AssetPool 里看是不是已经有了
```
AssetObject assetObject = m_ResourceLoader.m_AssetPool.Spawn(m_Task.AssetName);

```

他存在于的 Resource 是不是有了
```
ResourceObject resourceObject = m_ResourceLoader.m_ResourcePool.Spawn(resourceName);

```

没有的话就去读取 Resource
UseFileSystem = false，走下面，直接调用 ab 包 AssetBundle.LoadFromFileAsync


所以 fbx ab 包依赖 Resource ab 包的加载。每个 asset 在 unity 中的 dependency 被代替为 assetA -> assetA所在的 resource + assetA -> assetB -> assetB 所在的 resource

fullPath:
"D:/UnityProjects/GF_X/GF_X/BuildApp/StandaloneWindows64/GF_X_Data/StreamingAssets/DynamicAnimation.dat"

```
if (resourceInfo.LoadType == LoadType.LoadFromFile)
{
    if (resourceInfo.UseFileSystem)
    {
        IFileSystem fileSystem = m_ResourceLoader.m_ResourceManager.GetFileSystem(resourceInfo.FileSystemName, resourceInfo.StorageInReadOnly);
        m_Helper.ReadFile(fileSystem, resourceInfo.ResourceName.FullName);
    }
    else
    {
        m_Helper.ReadFile(fullPath);
    }
}
```
正常情况下，resourceInfo.UseFileSystem 应当 = true
使用 offset 来读取一个 文件系统中的 文件的 offset 部分
```
public override void ReadFile(IFileSystem fileSystem, string name)
{
    FileInfo fileInfo = fileSystem.GetFileInfo(name);
    m_FileFullPath = fileSystem.FullPath;
    m_FileName = name;
    m_FileAssetBundleCreateRequest = AssetBundle.LoadFromFileAsync(fileSystem.FullPath, 0u, (ulong)fileInfo.Offset);
}
```



## 读取资源文件 DefaultLoadResourceAgentHelper.ReadFile
这里是 DynamicAnimation.dat

```
/// <summary>
/// 通过加载资源代理辅助器开始异步读取资源文件。
/// </summary>
/// <param name="fullPath">要加载资源的完整路径名。</param>
public override void ReadFile(string fullPath)
{
    if (m_LoadResourceAgentHelperReadFileCompleteEventHandler == null || m_LoadResourceAgentHelperUpdateEventHandler == null || m_LoadResourceAgentHelperErrorEventHandler == null)
    {
        Log.Fatal("Load resource agent helper handler is invalid.");
        return;
    }

    m_FileFullPath = fullPath;
    m_FileAssetBundleCreateRequest = AssetBundle.LoadFromFileAsync(fullPath);
    

}
```

注意对于 resource 文件使用的是 
LoadFromFileAsync 而不是 LoadAssetAsync



## 资源读取完成 OnLoadResourceAgentHelperReadFileComplete 


```
LoadResourceAgent:OnLoadResourceAgentHelperReadFileComplete 296
DefaultLoadResourceAgentHelper:UpdateFileAssetBundleCreateRequest 500
DefaultLoadResourceAgentHelper:Update 407
```

```
private void OnLoadResourceAgentHelperReadFileComplete(object sender, LoadResourceAgentHelperReadFileCompleteEventArgs e)
{
//创建资源对象，ResourceObject类型
    ResourceObject resourceObject = ResourceObject.Create(m_Task.ResourceInfo.ResourceName.Name, e.Resource, m_ResourceHelper, m_ResourceLoader);
    
//把资源对象注册到 ResourcePool 
    m_ResourceLoader.m_ResourcePool.Register(resourceObject, true);
    s_LoadingResourceNames.Remove(m_Task.ResourceInfo.ResourceName.Name);
    
//调用 m_Task.LoadMain(LoadResourceAgent, resourceObject)，继续处理具体要加载的资产（fbx)
    OnResourceObjectReady(resourceObject);
}
```



## 创建资源对象
Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.ResourceObject.cs
```
public static ResourceObject Create(string name, object target, IResourceHelper resourceHelper, ResourceLoader resourceLoader)
{
    ResourceObject resourceObject = ReferencePool.Acquire<ResourceObject>();
    resourceObject.Initialize(name, target);
    //name = "DynamicAnimation"
    //target = "dynamicanimation (UnityEngine.AssetBundle)"

    resourceObject.m_ResourceHelper = resourceHelper;
    resourceObject.m_ResourceLoader = resourceLoader;
    return resourceObject;
}
```
这里的 target 的类型，说明 DynamicAnimation 这个 Resource 就是一个 AssetBundle


## m_Task.LoadMain
Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.LoadResourceTaskBase.cs
```
 agent.Helper.LoadAsset(resourceObject.Target, AssetName, AssetType, IsScene);
```
这里的 Helper 就是 DefaultLoadResourceAgentHelper
**到这里完成  ResourceManager.ResourceLoader.LoadAsset 到 DefaultLoadResourceAgentHelper.ReadFile 的链路**

```
public override void LoadAsset(object resource, string assetName, Type assetType, bool isScene)
{
//把刚才加载的 DynamicAnimation Resource 转换为 assetBundle
//这里的参数 resource 就是刚才创建的资源对象 ResourceObject
            AssetBundle assetBundle = resource as AssetBundle;

//这里 assetName = "Assets/AAAGame/DynamicAnimation/test_strech_squash_2020_6.fbx"
            m_AssetName = assetName;

//真正调用 AssetBundle Load 去加载 ab
// assetType = {UnityEngine.AnimationClip}
            m_AssetBundleRequest = assetBundle.LoadAssetAsync(assetName, assetType);

//Request 会被缓存在 m_AssetBundleRequest 中，然后在 UpdateAssetBundleRequest 时轮询是否完成加载

}

```

## DefaultLoadResourceAgentHelper.UpdateAssetBundleRequest

```
LoadResourceAgentHelperLoadCompleteEventArgs loadResourceAgentHelperLoadCompleteEventArgs = LoadResourceAgentHelperLoadCompleteEventArgs.Create(m_AssetBundleRequest.asset);
// 把加载好的 Asset 引用传给 loadResourceAgentHelperLoadCompleteEventArgs
// loadResourceAgentHelperLoadCompleteEventArgs.Asset = asset;


m_LoadResourceAgentHelperLoadCompleteEventHandler(this, loadResourceAgentHelperLoadCompleteEventArgs);

ReferencePool.Release(loadResourceAgentHelperLoadCompleteEventArgs);
m_AssetName = null;
m_LastProgress = 0f;
m_AssetBundleRequest = null;
```


## 在 TaskPool 初始化的时候，已经为 LoadResourceAgent 分配了回调

```
//LoadResourceAgent
public void Initialize()
{
     m_Helper.LoadResourceAgentHelperLoadComplete += OnLoadResourceAgentHelperLoadComplete;

}
```

Helper 的 m_LoadResourceAgentHelperLoadCompleteEventHandler = LoadResourceAgentHelperLoadComplete

## 回调 OnLoadResourceAgentHelperLoadComplete

```
private void OnLoadResourceAgentHelperLoadComplete(object sender, LoadResourceAgentHelperLoadCompleteEventArgs e)
//sender : DefaultLoadResourceAgentHelper
//LoadResourceAgentHelperLoadCompleteEventArgs.asset  加载完的 fbx 资产
{
    
//查看是否有 dependencyAssets
    List<object> dependencyAssets = m_Task.GetDependencyAssets();

//创建 AssetObject
//ResourceManager.ResourceLoader.AssetObject
    assetObject = AssetObject.Create(m_Task.AssetName, e.Asset, dependencyAssets, m_Task.ResourceObject.Target, m_ResourceHelper, m_ResourceLoader);

//注册到AssetPool, AssetToResourceMap
    m_ResourceLoader.m_AssetPool.Register(assetObject, true);
    m_ResourceLoader.m_AssetToResourceMap.Add(e.Asset, m_Task.ResourceObject.Target);

//如果 dependencyAsset 中有资产依赖其他的 ResouceB，那么让当前的 ResourceA 也依赖 ResourceB
foreach (object dependencyAsset in dependencyAssets)
{
    object dependencyResource = null;
    if (m_ResourceLoader.m_AssetToResourceMap.TryGetValue(dependencyAsset, out dependencyResource))
    {
        m_Task.ResourceObject.AddDependencyResource(dependencyResource);
    }
}

//回调资产加载时输入的自定义回调
OnAssetObjectReady(assetObject);

// object asset = assetObject.Target;  //真正返回的 asset 类型（AnimationClip）对象
//m_Task.OnLoadAssetSuccess(this, asset, (float)(DateTime.UtcNow - m_Task.StartTime).TotalSeconds);

}
```


# 最终回调 LoadAssetTask OnLoadAssetSuccess 
```
public override void OnLoadAssetSuccess(LoadResourceAgent agent, object asset, float duration)
{
    base.OnLoadAssetSuccess(agent, asset, duration);   //空函数
    
//m_LoadAssetCallbacks 中有对应 Asset 加载各种情况的 callback，这里是 success
//LoadAssetSuccessCallback 就是传入的自定义成功后 cb
    if (m_LoadAssetCallbacks.LoadAssetSuccessCallback != null)
    {
        m_LoadAssetCallbacks.LoadAssetSuccessCallback(AssetName, asset, duration, UserData);
        
//AssetName = "Assets/AAAGame/DynamicAnimation/test_strech_squash_2020_6.fbx"
//asset : AnimationClip Object
//duration : 13929
//UserData : null
    }
}
```

回调堆栈
```
Void <>c:<StartLoadingClip>b__2_0 (String, Object, Single, Object)+0x1 at LoadFbxClipExample 38
LoadAssetTask:OnLoadAssetSuccess 52
LoadResourceAgent:OnAssetObjectReady 271
LoadResourceAgent:OnLoadResourceAgentHelperLoadComplete 351
DefaultLoadResourceAgentHelper:UpdateAssetBundleRequest 570
DefaultLoadResourceAgentHelper:Update 409
```



查看代码说明，为什么GameFramework 打包过程中，要在 ab 包的基础上再额外使用一种 dat                        
文件？在没有任何加密的情况下，使用LoadFromFile去打 ResourceEditor 中的各个资源，例如                        dynanmicAnimation.dat，这个dat文件其中包含了多少 ab 包？test_strech_squash_2020_6.fbx 这个 fbx 文件被打成 ab 包之后，直接存放于 dat 文件内部吗？为什么加载时先把 dynamicAnimation.dat 作为 ab 包加载，然后又去加载 fbx 文件的 ab 包呢？ 



# Http服务器上的文件和 StreamingAssets 中的同前缀文件的关系

GF_X\BuildApp\StandaloneWindows64\GF_X_Data\StreamingAssets
DynamicAnimation.dat 的开头是 UnityFS    5.x.x 2022.3.55f1c1，说明他符合 ab 包格式。
Entity.dat 开头也是 UnityFS，尽管他包含了多个 prefab 在内，但他也是符合 ab 包格式

GF_X\AB\Full\1_0_0_1\Windows64\DynamicAnimation.8254ae21.dat
GF_X\AB\Full\1_0_0_1\Windows64\Entity.50584b9d.dat
这两个文件里面都是乱码，说明他们不是 ab 包格式。

当我标记为 Updatable 打包的时候，StreamingAssets 应当是去我架设的本地 http 服务器中下载？我的 http 服务器中映射了 1_0_0_1 文件夹。

尝试说明从  1_0_0_1\Windows64 中的文件到 StreamingAssets 过程中为什么会发生变化？或者说 StreamingAssets 根本没有走下载？



   1. 构建目录 (`AB\Full\1_0_0_1\Windows64`):
       * 这是资源构建（Build Resource）过程的直接产物。
       * 默认情况下，为了防止资源被轻易解包和盗用，GameFramework会对生成的AssetBundle（AB包）进行加密或偏移处理。
         这就是为什么你直接用文本编辑器打开这些.dat文件会看到“乱码”，并且找不到"UnityFS"文件头。它们本质上仍然是AB包，只是被“加工”过。

   2. 随包资源目录 (`StreamingAssets`):
       * 这是构建应用（Build App）时，从上述构建目录中拷贝过来的。这些资源将作为你应用的“初始版本”或“基础包”。
       * 当应用启动时，它会首先从这个只读的StreamingAssets目录中加载必要的资源。
       * 在拷贝过程中，GameFramework会进行一次处理，解密或恢复偏移，将它们还原成标准的AB包格式。这就是为什么你在StreamingAssets里的.dat文件中能看到"UnityFS"文件头。
       

AssetStudio 对于这两种文件都能打开，说明他们都是可识别的 ab 包格式。


# 关卡实体的加载

调用栈
```
LoadAssetTask:Create 35
ResourceLoader:LoadAsset 334
ResourceManager:LoadAsset 1604
EntityManager:ShowEntity 651
EntityComponent:ShowEntity 494
EntityComponent:ShowEntity 474
EntityExtension:ShowEntity 178
EntityExtension:ShowEntity 193
AwaitExtension:ShowEntityAwait 90
d__10:MoveNext 87
MenuProcedure:OnEnter 24
1:ChangeState 585
1:ChangeState 562
1:ChangeState 81
ChangeSceneProcedure:OnUpdate 62
1:Update 545
FsmManager:Update 78
GameFrameworkEntry:Update 29
BaseComponent:Update 231
```

## MenuProcedure
```
protected override void OnEnter(IFsm<IProcedureManager> procedureOwner)
{
        ShowLevel();//加载关卡
}
```


## 关卡 prefab
```
public async void ShowLevel()
    {
...
//创建关卡对应的 prefab
        var lvParams = EntityParams.Create(Vector3.zero, Vector3.zero, Vector3.one);
        lvParams.Set(LevelEntity.P_LevelData, lvRow);
        
//LvPfbName = "Lv_1"
        lvEntity = await GF.Entity.ShowEntityAwait<LevelEntity>(lvRow.LvPfbName, Const.EntityGroup.Level, lvParams) as LevelEntity;
        
    }
```

```
/// <summary>
/// 显示实体。
/// </summary>
/// <typeparam name="T">实体逻辑类型。</typeparam>
/// <param name="entityId">实体编号。</param>
/// <param name="entityAssetName">实体资源名称。</param>
/// <param name="entityGroupName">实体组名称。</param>
/// <param name="priority">加载实体资源的优先级。</param>
/// <param name="userData">用户自定义数据。</param>
public void ShowEntity<T>(int entityId, string entityAssetName, string entityGroupName, int priority, object userData) where T : EntityLogic
{
    ShowEntity(entityId, typeof(T), entityAssetName, entityGroupName, priority, userData);
}
entityAssetName = "Assets/AAAGame/Prefabs/Entity/Lv_1.prefab"
```

## 关卡实体关联加载 Entity.dat

m_Task.AssetName = "Assets/AAAGame/Prefabs/Entity/Lv_1.prefab"
resourceInfo.ResourceName = "Entity.dat"
resourceInfo.ResourceName.Name = "Entity"
Entity.dat 走的也是 UseFileSystem = false。



  所以，整个流程可以简化为两个核心的异步步骤：

AssetBundle.LoadFromFileAsync(...)：将整个 Entity.dat 文件加载为内存中的 AssetBundle 对象。
AssetBundle.LoadAssetAsync<GameObject>("xxx.prefab")：从上一步得到的 AssetBundle 对象中，异步提取出单个 GameObject 资产。


# MyPlayer.prefab 的加载


## ShowEntity
```
public void ShowEntity(int entityId, string entityAssetName, string entityGroupName, int priority, object userData)
{
     m_ResourceManager.LoadAsset(entityAssetName, priority, m_LoadAssetCallbacks, ShowEntityInfo.Create(serialId, entityId, entityGroup, userData));

}

```
entityId = 4
entityAssetName = "Assets/AAAGame/Prefabs/Entity/MyPlayer.prefab"
userData 里带了出生时需要的信息，例如 position, rotation, attachToEntity



## LoadAssetTask 创建
```
LoadAssetTask:Create 35
ResourceLoader:LoadAsset 334
ResourceManager:LoadAsset 1604
EntityManager:ShowEntity 651
EntityComponent:ShowEntity 494
EntityComponent:ShowEntity 474
EntityExtension:ShowEntity 178
EntityExtension:ShowEntity 193
AwaitExtension:ShowEntityAwait 90
d__13:MoveNext 48
Entity:OnShow 166
EntityManager:InternalShowEntity 1179
EntityManager:LoadAssetSuccessCallback 1264
LoadAssetTask:OnLoadAssetSuccess 52
LoadResourceAgent:OnAssetObjectReady 271
LoadResourceAgent:OnLoadResourceAgentHelperLoadComplete 351
DefaultLoadResourceAgentHelper:UpdateAssetBundleRequest 570
DefaultLoadResourceAgentHelper:Update 409
```

assetName = "Assets/AAAGame/Prefabs/Entity/MyPlayer.prefab"
assetType = null
resourceInfo
FileSystemName = null
loadType = LoadFromFile
ResourceName = "Entity.dat"


