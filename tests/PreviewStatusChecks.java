import org.helixsequencer.android.PreviewStatus;

/** Host check for the phone preview gate. Not an Android instrumentation test. */
public class PreviewStatusChecks {
    public static void main(String[] args) {
        expect(PreviewStatus.canPlay("completed", true), "completed file plays");
        expect(!PreviewStatus.canPlay("completed", false), "missing file does not play");
        expect(!PreviewStatus.canPlay("failed", true), "failed file does not play");
        expect(!PreviewStatus.canPlay("pending", true), "pending file does not play");
        expect(!PreviewStatus.canPlay("running", true), "running file does not play");
        expect(!PreviewStatus.canPlay("unavailable", true), "unavailable file does not play");
        expect(PreviewStatus.canPlay("", true), "legacy checkpoint still plays");
        expect(PreviewStatus.canPlay(null, true), "missing state still plays");
        expect(PreviewStatus.label("failed").contains("sequence can still be saved"), "failed copy");
        expect(PreviewStatus.label("unavailable").contains("sequence can still be saved"), "unavailable copy");
        expect(PreviewStatus.label("completed").contains("simulated"), "simulated label");
        expect(PreviewStatus.label("pending").contains("Sequence export"), "pending copy");
        System.out.println("PreviewStatusChecks ok");
    }

    private static void expect(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
}
