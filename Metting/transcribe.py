# meet/transcribe.py
import tempfile, os, json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from googletrans import Translator
import whisper

# load model once (choose small/medium/large as needed)
MODEL = whisper.load_model("small")
TRANS = Translator()

@csrf_exempt
def transcribe_and_translate(request):
    """
    POST multipart/form-data with 'file' (wav/webm/m4a) and optional 'translate_to' (e.g. 'hi', 'te', 'ta')
    Returns JSON: { text: "...", translations: { hi: "...", ... }, speaker: "Guest" }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    if 'file' not in request.FILES:
        return HttpResponseBadRequest("missing file")

    f = request.FILES['file']
    dest = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.name)[1])
    try:
        for chunk in f.chunks():
            dest.write(chunk)
        dest.flush()
        dest.close()

        # whisper transcription (you can remove language to auto-detect)
        try:
            res = MODEL.transcribe(dest.name)  # let whisper auto-detect
            text = res.get("text", "").strip()
        except Exception as e:
            text = ""
            # log in real app
            print("whisper transcribe error:", e)

        # translations requested: "translate_to" may be 'none' or specific language code
        requested = request.POST.get("translate_to", "").strip()
        translations = {}

        # if requested is "none" we still return translations for common languages optionally
        try:
            # if explicit requested language, only return that plus a small set
            langs_to_return = []
            if requested and requested.lower() != "none":
                langs_to_return = [requested]
            # also include the common trio so client has options
            for lang in ("hi","te","ta"):
                if lang not in langs_to_return:
                    langs_to_return.append(lang)
            # produce translations
            for lang in langs_to_return:
                try:
                    tr = TRANS.translate(text, dest=lang)
                    translations[lang] = tr.text
                except Exception:
                    translations[lang] = ""
        except Exception:
            translations = {}

        # optional speaker field -- if client sends "speaker" in form we echo; else fallback to "Guest"
        speaker = request.POST.get("speaker") or request.POST.get("name") or "Guest"

        return JsonResponse({"text": text, "translations": translations, "speaker": speaker})
    finally:
        try:
            os.unlink(dest.name)
        except Exception:
            pass
