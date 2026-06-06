import SvgIcon from './SvgIcon'
import IconLink from './IconLink'

function LinkSection({ id, iconHref, title, subtitle, links }) {
  return (
    <div id={id}>
      <SvgIcon href={iconHref} className="icon" />
      <h2>{title}</h2>
      <p>{subtitle}</p>
      <ul>
        {links.map((link) => (
          <IconLink key={link.label} {...link} />
        ))}
      </ul>
    </div>
  )
}

export default LinkSection
