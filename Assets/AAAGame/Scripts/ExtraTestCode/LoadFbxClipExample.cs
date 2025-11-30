using UnityEngine;
using GameFramework;
using GameFramework.Resource;
using UnityGameFramework.Runtime;

public class LoadFbxClipExample : MonoBehaviour
{
    public void Awake()
    {
        StartCoroutine(DelayedStart());
    }

    private System.Collections.IEnumerator DelayedStart()
    {
        yield return new WaitForSeconds(30);
        StartLoadingClip();
    }

    // 调用此方法来开始加载
    public void StartLoadingClip()
    {
        // FBX 文件在项目中的完整资产路径
        string fbxAssetPath = "Assets/AAAGame/DynamicAnimation/test_strech_squash_2020_6.fbx";

        Log.Info($"Attempting to load AnimationClip from: {fbxAssetPath}");

        // 使用资源组件加载资产
        // 资产名称使用 FBX 的路径
        // 资产类型指定为 AnimationClip
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
    }
}