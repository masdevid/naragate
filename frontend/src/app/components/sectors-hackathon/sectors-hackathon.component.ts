import { ChangeDetectionStrategy, Component } from '@angular/core';
import { TPipe } from '../../pipes/t.pipe';

@Component({
  selector: 'app-sectors-hackathon',
  standalone: true,
  imports: [TPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <a href="https://hackathon.sectors.app" target="_blank" rel="noopener"
      class="flex min-w-0 shrink items-center gap-3 sm:shrink-0">
      <img alt="" loading="lazy" width="20" height="24" decoding="async" class="h-6 w-5"
        src="https://hackathon.sectors.app/brand/sectors-icon.svg" style="color: transparent;">
      <span class="min-w-0">
        <span class="block text-sm font-bold leading-none tracking-tight">{{ 'footer.sectors' | t }}</span>
        <span class="mt-1 hidden font-mono text-xs font-semibold uppercase tracking-[0.16em]
          text-muted min-[368px]:block">{{ 'footer.sectors_track' | t }}</span>
      </span>
    </a>
  `,
})
export class SectorsHackathonComponent {}