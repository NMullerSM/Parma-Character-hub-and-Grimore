// TaleSpire BepInEx Plugin: AutoThrowPatch.cs
// Ingeniería inversa realizada sobre: TaleSpire_Data/Managed/Bouncyrock.TaleSpire.Runtime.dll
// Detecta la recepción de tiradas mediante IPC (SetDiceUrl) y ejecuta automáticamente el lanzamiento
// físico en la mesa 3D sin mover el ratón del usuario ni secuestrar el cursor.

using BepInEx;
using HarmonyLib;
using UnityEngine;
using Unity.Mathematics;

namespace TaleSpireAutoThrow
{
    [BepInPlugin("com.dndvisualizer.autothrow", "TaleSpire Auto Throw Plugin", "1.1.0")]
    [BepInProcess("TaleSpire.exe")]
    public class AutoThrowPlugin : BaseUnityPlugin
    {
        void Awake()
        {
            var harmony = new Harmony("com.dndvisualizer.autothrow");
            harmony.PatchAll();
            Logger.LogInfo("[AutoThrow] TaleSpire Auto-Throw Bridge inicializado con éxito.");
        }
    }

    /// <summary>
    /// Hook sobre UIDiceTray.SetDiceUrl: Se ejecuta en cuanto TaleSpire recibe los dados del Pipe IPC.
    /// </summary>
    [HarmonyPatch(typeof(UIDiceTray), "SetDiceUrl", typeof(DiceRollDescriptor), typeof(bool))]
    public static class AutoThrowTrayPatch
    {
        public static void Postfix(UIDiceTray __instance, RollId __result)
        {
            if (__instance == null || !__result.IsValid)
                return;

            try
            {
                // 1. Spawnea los dados físicamente en el mundo 3D y activa DiceBoardTool
                __instance.Spawn(false);

                // 2. Imparte impulso físico hacia el centro del tablero 3D (X: 0, Y: +3.5m/s elevación, Z: +12m/s avance)
                float3 throwVelocity = new float3(0f, 3.5f, 12.0f);
                Dice.DiceRollManager.Instance.ThrowDice(__result, throwVelocity);

                // 3. Devuelve la herramienta activa al tablero por defecto
                BoardToolManager.Instance.SwitchToTool(null);
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[AutoThrow] Error al expulsar dados automáticamente: {ex.Message}");
            }
        }
    }
}
