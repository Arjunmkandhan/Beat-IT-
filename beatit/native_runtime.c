/* Fixed native support library. Generated assembly calls these functions. */
#include <windows.h>
#include <mmsystem.h>
#include <stdio.h>
#include <string.h>

static unsigned long g_async_count = 0;

void beatit_set_volume(unsigned long vol_percent) {
    if (vol_percent > 100) vol_percent = 100;
    DWORD channel_vol = (vol_percent * 0xFFFF) / 100;
    DWORD lr_vol = (channel_vol << 16) | channel_vol;
    waveOutSetVolume(NULL, lr_vol);
}

// Accepts 4 arguments via x64 calling convention: rcx=relative, rdx=start_ms, r8=end_ms, r9=is_async
void beatit_play(const char *relative, unsigned long start_ms, unsigned long end_ms, int is_async) {
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    char *last = strrchr(path, '\\');
    if (last) *(last + 1) = '\0';
    strncat(path, relative, MAX_PATH - strlen(path) - 1);

    char cmd[MAX_PATH + 128];
    char alias[32];

    if (is_async) {
        snprintf(alias, sizeof(alias), "async_beat_%lu", g_async_count++);
    } else {
        snprintf(alias, sizeof(alias), "beat_sound");
        mciSendStringA("close beat_sound", NULL, 0, NULL);
    }

    snprintf(cmd, sizeof(cmd), "open \"%s\" alias %s", path, alias);
    if (mciSendStringA(cmd, NULL, 0, NULL) != 0) {
        fprintf(stderr, "Beat It runtime: cannot open %s\n", path);
        return;
    }

    snprintf(cmd, sizeof(cmd), "set %s time format milliseconds", alias);
    mciSendStringA(cmd, NULL, 0, NULL);

    const char *wait_str = is_async ? "" : " wait";

    if (end_ms > 0 && end_ms > start_ms) {
        snprintf(cmd, sizeof(cmd), "play %s from %lu to %lu%s", alias, start_ms, end_ms, wait_str);
    } else if (start_ms > 0) {
        snprintf(cmd, sizeof(cmd), "play %s from %lu%s", alias, start_ms, wait_str);
    } else {
        snprintf(cmd, sizeof(cmd), "play %s%s", alias, wait_str);
    }

    mciSendStringA(cmd, NULL, 0, NULL);

    if (!is_async) {
        mciSendStringA("close beat_sound", NULL, 0, NULL);
    }
}

void beatit_sleep(unsigned long milliseconds) {
    Sleep(milliseconds);
}