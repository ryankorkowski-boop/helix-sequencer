package org.helixsequencer.android;

/** Playback gate for checkpointed variant previews. An empty state keeps older checkpoints playable. */
public final class PreviewStatus {
    private PreviewStatus(){}

    public static boolean canPlay(String state, boolean fileExists){
        if(!fileExists)return false;
        if(state==null||state.isEmpty())return true;
        return "completed".equals(state);
    }

    public static String label(String state){
        if(state==null||state.isEmpty())return "Preview status was not reported. Playback uses the file on disk.";
        switch(state){
            case "completed": return "Preview ready. This is a simulated phone render, not native xLights.";
            case "running": return "Preview encoding. You can play variants that already finished.";
            case "pending": return "Preview waiting. Sequence export is already available.";
            case "failed": return "Preview failed. The sequence can still be saved.";
            case "unavailable": return "No preview was requested for this sequence. The sequence can still be saved.";
            default: return "Preview "+state;
        }
    }
}
